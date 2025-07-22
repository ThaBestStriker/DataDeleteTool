import sqlite3
import sqlcipher3
import os

def view_db(passphrase):
    """View entries in the broker_sites table with various options."""
    db_path = os.path.join('data', 'pii_data.db')
    conn = None
    try:
        conn = sqlcipher3.connect(db_path)
        cursor = conn.cursor()
        if passphrase:
            cursor.execute(f"PRAGMA key = '{passphrase}'")
            cursor.execute("PRAGMA kdf_iter = 64000")
            cursor.execute("PRAGMA cipher_page_size = 4096")
        cursor.execute("PRAGMA foreign_keys = ON")
        
        while True:
            print("\nView Entries Options:")
            print("1: Search by text")
            print("2: List all names with entry numbers")
            print("3: View entry by number")
            print("4: Back to main menu")
            choice = input("Enter choice (1-4): ").strip()
            
            if choice == '1':
                search_text = input("Enter search text: ").strip().lower()
                query = """
                SELECT * FROM broker_sites
                WHERE LOWER(name) LIKE ? OR LOWER(url) LIKE ? OR LOWER(deletion_url) LIKE ?
                OR LOWER(privacy_policy) LIKE ? OR LOWER(contact) LIKE ?
                OR LOWER(requirements) LIKE ? OR LOWER(notes) LIKE ?
                """
                cursor.execute(query, (f'%{search_text}%',) * 7)
                results = cursor.fetchall()
                if not results:
                    print("No entries found matching the search text.")
                else:
                    print(f"\nFound {len(results)} entries:")
                    for row in results:
                        print("\nEntry:")
                        print(f"Site ID: {row[0]}")
                        print(f"Name: {row[1]}")
                        print(f"URL: {row[2] or 'None'}")
                        print(f"Deletion URL: {row[3] or 'None'}")
                        print(f"Privacy Policy: {row[4] or 'None'}")
                        print(f"Contact: {row[5] or 'None'}")
                        print(f"Requirements: {row[6] or 'None'}")
                        print(f"Notes: {row[7] or 'None'}")
                        print(f"Last Updated: {row[8] or 'None'}")
            
            elif choice == '2':
                cursor.execute("SELECT site_id, name FROM broker_sites ORDER BY site_id")
                results = cursor.fetchall()
                if not results:
                    print("No entries in broker_sites.")
                else:
                    print(f"\nListing {len(results)} entries:")
                    for row in results:
                        print(f"Entry {row[0]}: {row[1]}")
            
            elif choice == '3':
                try:
                    site_id = int(input("Enter entry number (site_id): ").strip())
                    cursor.execute("SELECT * FROM broker_sites WHERE site_id = ?", (site_id,))
                    row = cursor.fetchone()
                    if row:
                        print("\nEntry:")
                        print(f"Site ID: {row[0]}")
                        print(f"Name: {row[1]}")
                        print(f"URL: {row[2] or 'None'}")
                        print(f"Deletion URL: {row[3] or 'None'}")
                        print(f"Privacy Policy: {row[4] or 'None'}")
                        print(f"Contact: {row[5] or 'None'}")
                        print(f"Requirements: {row[6] or 'None'}")
                        print(f"Notes: {row[7] or 'None'}")
                        print(f"Last Updated: {row[8] or 'None'}")
                    else:
                        print(f"No entry found with site_id {site_id}.")
                except ValueError:
                    print("Invalid entry number. Please enter a numeric site_id.")
            
            elif choice == '4':
                break
            else:
                print("Invalid choice. Please enter 1-4.")
    
    except Exception as e:
        print(f"Error querying database: {e}")
    finally:
        if conn:
            conn.close()