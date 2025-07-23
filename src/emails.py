import sqlite3
import sqlcipher3
import os
import signal

def signal_handler(sig, frame):
    """Handle Ctrl+S to skip input."""
    raise KeyboardInterrupt

def modify_emails(passphrase, user_id):
    """Modify email information for a specific user_id."""
    db_path = os.path.join('data', 'pii_data.db')
    conn = None
    try:
        conn = sqlcipher3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA key = '{passphrase}'")
        cursor.execute("PRAGMA kdf_iter = 64000")
        cursor.execute("PRAGMA cipher_page_size = 4096")
        cursor.execute("PRAGMA foreign_keys = ON")
        
        while True:
            print("\nEmail Options:")
            print("1: Add new email")
            print("2: View existing emails")
            print("3: Delete email")
            print("4: Back to modify user menu")
            choice = input("Enter choice (1-4): ").strip()
            
            if choice == '1':
                signal.signal(signal.SIGTSTP, signal_handler)
                email_address = None
                source_site = None
                is_active = None
                try:
                    email_address = input("Email Address: ").strip() or None
                except KeyboardInterrupt:
                    email_address = None
                try:
                    source_site = input("Source Site (optional): ").strip() or None
                except KeyboardInterrupt:
                    source_site = None
                try:
                    is_active_input = input("Is active email (y/N)? ").strip().lower()
                    is_active = 1 if is_active_input == 'y' else 0
                except KeyboardInterrupt:
                    is_active = 0
                signal.signal(signal.SIGTSTP, signal.SIG_DFL)
                
                if not email_address:
                    print("Email address is required.")
                    continue
                
                cursor.execute("""
                INSERT INTO emails (user_id, email_address, source_site, is_active)
                VALUES (?, ?, ?, ?)
                """, (user_id, email_address, source_site, is_active))
                conn.commit()
                print("Email added.")
            
            elif choice == '2':
                cursor.execute("SELECT email_id, email_address, source_site, is_active FROM emails WHERE user_id = ?", (user_id,))
                emails = cursor.fetchall()
                if not emails:
                    print("No emails found for this user.")
                else:
                    print("\nEmails:")
                    for email in emails:
                        email_id, email_address, source_site, is_active = email
                        print(f"Email ID: {email_id}")
                        print(f"Email Address: {email_address}")
                        print(f"Source Site: {source_site or 'None'}")
                        print(f"Active: {'Yes' if is_active else 'No'}")
                        print()
            
            elif choice == '3':
                cursor.execute("SELECT email_id, email_address FROM emails WHERE user_id = ?", (user_id,))
                emails = cursor.fetchall()
                if not emails:
                    print("No emails found for this user.")
                    continue
                print("\nEmails:")
                for email in emails:
                    email_id, email_address = email
                    print(f"Email ID: {email_id}, {email_address}")
                try:
                    email_id = int(input("Enter email_id to delete: ").strip())
                    cursor.execute("SELECT 1 FROM emails WHERE email_id = ? AND user_id = ?", (email_id, user_id))
                    if not cursor.fetchone():
                        print(f"No email found with email_id {email_id} for this user.")
                        continue
                    cursor.execute("DELETE FROM emails WHERE email_id = ?", (email_id,))
                    conn.commit()
                    print(f"Email ID {email_id} deleted.")
                except ValueError:
                    print("Invalid email_id. Please enter a numeric value.")
            
            elif choice == '4':
                break
            else:
                print("Invalid choice. Please enter 1-4.")
    
    except Exception as e:
        print(f"Error managing emails: {e}")
    finally:
        if conn:
            conn.close()