import sqlite3
import sqlcipher3
import os
import datetime
import webbrowser

def cleaning(passphrase):
    """Manage cleaning requests for broker sites."""
    db_path = os.path.join('data', 'pii_data.db')
    conn = None
    try:
        conn = sqlcipher3.connect(db_path)
        cursor = conn.cursor()
        if passphrase:
            conn.execute(f"PRAGMA key = '{passphrase}'")
            conn.execute("PRAGMA kdf_iter = 64000")
            conn.execute("PRAGMA cipher_page_size = 4096")
        conn.execute("PRAGMA foreign_keys = ON")
        
        while True:
            print("\nCleaning Options:")
            print("1: Add cleaning request")
            print("2: Automated cleaning")
            print("3: Confirm deletion")
            print("4: Show status counts (Clean, Expired, Needs Verification)")
            print("5: Back to main menu")
            choice = input("Enter choice (1-5): ").strip()
            
            if choice == '1':
                try:
                    site_id = int(input("Enter site_id (use 'database > view entries' to find): ").strip())
                    cursor.execute("SELECT name FROM broker_sites WHERE site_id = ?", (site_id,))
                    site = cursor.fetchone()
                    if not site:
                        print(f"No site found with site_id {site_id}.")
                        continue
                    site_name = site[0]
                    date_cleaned = datetime.date.today().isoformat()
                    cursor.execute("""
                    INSERT OR REPLACE INTO cleaning_records (site_id, site_name, date_cleaned, date_confirmed_deleted)
                    VALUES (?, ?, ?, NULL)
                    """, (site_id, site_name, date_cleaned))
                    conn.commit()
                    print(f"Cleaning request added for {site_name} (site_id: {site_id}).")
                except ValueError:
                    print("Invalid site_id. Please enter a numeric value.")
                except sqlite3.IntegrityError:
                    print(f"Cleaning request already exists for site_id {site_id}.")
            
            elif choice == '2':
                today = datetime.date.today()
                # Get expired entries
                cursor.execute("""
                SELECT bs.site_id, bs.name, bs.url, bs.deletion_url
                FROM broker_sites bs
                LEFT JOIN cleaning_records cr ON bs.site_id = cr.site_id
                WHERE cr.site_id IS NULL
                   OR cr.date_confirmed_deleted IS NULL AND cr.date_cleaned IS NULL
                   OR (cr.date_confirmed_deleted IS NOT NULL AND julianday(?) - julianday(cr.date_confirmed_deleted) > 183)
                """, (today.isoformat(),))
                expired_entries = cursor.fetchall()
                
                # Get status counts
                clean_count = 0
                expired_count = len(expired_entries)
                needs_verification_count = 0
                
                cursor.execute("SELECT site_id, site_name, date_cleaned, date_confirmed_deleted FROM cleaning_records")
                records = cursor.fetchall()
                for record in records:
                    site_id, site_name, date_cleaned, date_confirmed_deleted = record
                    cleaned_date = datetime.date.fromisoformat(date_cleaned) if date_cleaned else None
                    verified_date = datetime.date.fromisoformat(date_confirmed_deleted) if date_confirmed_deleted else None
                    
                    if verified_date:
                        days_since_verified = (today - verified_date).days
                        if days_since_verified <= 183:
                            clean_count += 1
                        else:
                            expired_count += 1
                    elif cleaned_date:
                        days_since_cleaned = (today - cleaned_date).days
                        if days_since_cleaned <= 30:
                            clean_count += 1
                        else:
                            needs_verification_count += 1
                
                print("\nStatus Counts:")
                print(f"Clean: {clean_count}")
                print(f"Expired: {expired_count}")
                print(f"Needs Verification: {needs_verification_count}")
                
                if not expired_entries:
                    print("No expired entries to clean.")
                    continue
                
                for site_id, site_name, url, deletion_url in expired_entries:
                    print(f"\nProcessing Expired Entry:")
                    print(f"Site ID: {site_id}")
                    print(f"Name: {site_name}")
                    print(f"URL: {url or 'None'}")
                    print(f"Deletion URL: {deletion_url or 'None'}")
                    
                    # Open URL in Firefox
                    if url and url != 'None':
                        try:
                            webbrowser.get('firefox').open_new_tab(url)
                            print(f"Opened {url} in new Firefox tab")
                        except webbrowser.Error:
                            print("Error opening Firefox. Please visit the URL manually.")
                    
                    # Prompt for action
                    while True:
                        action = input("\nChoose action: (C)lean, (V)erified, (S)kip, (E)xit: ").strip().lower()
                        if action == 'c':
                            if deletion_url and deletion_url != 'None':
                                try:
                                    webbrowser.get('firefox').open_new_tab(deletion_url)
                                    print(f"Opened deletion URL {deletion_url} in new Firefox tab")
                                except webbrowser.Error:
                                    print(f"Error opening Firefox. Please visit deletion URL manually: {deletion_url}")
                            else:
                                print(f"No deletion URL available for {site_name}")
                            success = input("Success? (Y/n): ").strip().lower()
                            if success in ('y', ''):
                                date_cleaned = datetime.date.today().isoformat()
                                cursor.execute("""
                                INSERT OR REPLACE INTO cleaning_records (site_id, site_name, date_cleaned, date_confirmed_deleted)
                                VALUES (?, ?, ?, NULL)
                                """, (site_id, site_name, date_cleaned))
                                conn.commit()
                                print(f"Marked as cleaned for {site_name} (site_id: {site_id}).")
                            break
                        elif action == 'v':
                            date_cleaned = datetime.date.today().isoformat()
                            date_confirmed_deleted = datetime.date.today().isoformat()
                            cursor.execute("""
                            INSERT OR REPLACE INTO cleaning_records (site_id, site_name, date_cleaned, date_confirmed_deleted)
                            VALUES (?, ?, ?, ?)
                            """, (site_id, site_name, date_cleaned, date_confirmed_deleted))
                            conn.commit()
                            print(f"Marked as verified for {site_name} (site_id: {site_id}).")
                            break
                        elif action == 's':
                            print(f"Skipped {site_name} (site_id: {site_id}).")
                            break
                        elif action == 'e':
                            print("Exiting automated cleaning.")
                            return
                        else:
                            print("Invalid action. Please choose C, V, S, or E.")
            
            elif choice == '3':
                try:
                    site_id = int(input("Enter site_id to confirm deletion: ").strip())
                    cursor.execute("SELECT name FROM broker_sites WHERE site_id = ?", (site_id,))
                    site = cursor.fetchone()
                    if not site:
                        print(f"No site found with site_id {site_id}.")
                        continue
                    site_name = site[0]
                    cursor.execute("SELECT record_id FROM cleaning_records WHERE site_id = ?", (site_id,))
                    record = cursor.fetchone()
                    if not record:
                        print(f"No cleaning request found for {site_name} (site_id: {site_id}).")
                        continue
                    date_confirmed_deleted = datetime.date.today().isoformat()
                    cursor.execute("""
                    UPDATE cleaning_records
                    SET date_confirmed_deleted = ?
                    WHERE site_id = ?
                    """, (date_confirmed_deleted, site_id))
                    conn.commit()
                    print(f"Deletion confirmed for {site_name} (site_id: {site_id}).")
                except ValueError:
                    print("Invalid site_id. Please enter a numeric value.")
            
            elif choice == '4':
                today = datetime.date.today()
                clean_count = 0
                expired_count = 0
                needs_verification_count = 0
                
                cursor.execute("SELECT site_id, site_name, date_cleaned, date_confirmed_deleted FROM cleaning_records")
                records = cursor.fetchall()
                
                for record in records:
                    site_id, site_name, date_cleaned, date_confirmed_deleted = record
                    cleaned_date = datetime.date.fromisoformat(date_cleaned) if date_cleaned else None
                    verified_date = datetime.date.fromisoformat(date_confirmed_deleted) if date_confirmed_deleted else None
                    
                    if verified_date:
                        days_since_verified = (today - verified_date).days
                        if days_since_verified <= 183:
                            clean_count += 1
                        else:
                            expired_count += 1
                    elif cleaned_date:
                        days_since_cleaned = (today - cleaned_date).days
                        if days_since_cleaned <= 30:
                            clean_count += 1
                        else:
                            needs_verification_count += 1
                
                cursor.execute("SELECT COUNT(*) FROM broker_sites WHERE site_id NOT IN (SELECT site_id FROM cleaning_records)")
                untracked_count = cursor.fetchone()[0]
                expired_count += untracked_count
                
                print("\nStatus Counts:")
                print(f"Clean: {clean_count}")
                print(f"Expired: {expired_count}")
                print(f"Needs Verification: {needs_verification_count}")
            
            elif choice == '5':
                break
            else:
                print("Invalid choice. Please enter 1-5.")
    
    except Exception as e:
        print(f"Error managing cleaning records: {e}")
    finally:
        if conn:
            conn.close()