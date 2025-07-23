import sqlite3
import sqlcipher3
import os
import signal

def signal_handler(sig, frame):
    """Handle Ctrl+S to skip input."""
    raise KeyboardInterrupt

def modify_phone_numbers(passphrase, user_id):
    """Modify phone number information for a specific user_id."""
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
            print("\nPhone Number Options:")
            print("1: Add new phone number")
            print("2: View existing phone numbers")
            print("3: Delete phone number")
            print("4: Back to modify user menu")
            choice = input("Enter choice (1-4): ").strip()
            
            if choice == '1':
                signal.signal(signal.SIGTSTP, signal_handler)
                phone_number = None
                source_site = None
                is_active = None
                try:
                    phone_number = input("Phone Number: ").strip() or None
                except KeyboardInterrupt:
                    phone_number = None
                try:
                    source_site = input("Source Site (optional): ").strip() or None
                except KeyboardInterrupt:
                    source_site = None
                try:
                    is_active_input = input("Is active phone number (y/N)? ").strip().lower()
                    is_active = 1 if is_active_input == 'y' else 0
                except KeyboardInterrupt:
                    is_active = 0
                signal.signal(signal.SIGTSTP, signal.SIG_DFL)
                
                if not phone_number:
                    print("Phone number is required.")
                    continue
                
                cursor.execute("""
                INSERT INTO phone_numbers (user_id, phone_number, source_site, is_active)
                VALUES (?, ?, ?, ?)
                """, (user_id, phone_number, source_site, is_active))
                conn.commit()
                print("Phone number added.")
            
            elif choice == '2':
                cursor.execute("SELECT phone_id, phone_number, source_site, is_active FROM phone_numbers WHERE user_id = ?", (user_id,))
                phones = cursor.fetchall()
                if not phones:
                    print("No phone numbers found for this user.")
                else:
                    print("\nPhone Numbers:")
                    for phone in phones:
                        phone_id, phone_number, source_site, is_active = phone
                        print(f"Phone ID: {phone_id}")
                        print(f"Phone Number: {phone_number}")
                        print(f"Source Site: {source_site or 'None'}")
                        print(f"Active: {'Yes' if is_active else 'No'}")
                        print()
            
            elif choice == '3':
                cursor.execute("SELECT phone_id, phone_number FROM phone_numbers WHERE user_id = ?", (user_id,))
                phones = cursor.fetchall()
                if not phones:
                    print("No phone numbers found for this user.")
                    continue
                print("\nPhone Numbers:")
                for phone in phones:
                    phone_id, phone_number = phone
                    print(f"Phone ID: {phone_id}, {phone_number}")
                try:
                    phone_id = int(input("Enter phone_id to delete: ").strip())
                    cursor.execute("SELECT 1 FROM phone_numbers WHERE phone_id = ? AND user_id = ?", (phone_id, user_id))
                    if not cursor.fetchone():
                        print(f"No phone number found with phone_id {phone_id} for this user.")
                        continue
                    cursor.execute("DELETE FROM phone_numbers WHERE phone_id = ?", (phone_id,))
                    conn.commit()
                    print(f"Phone ID {phone_id} deleted.")
                except ValueError:
                    print("Invalid phone_id. Please enter a numeric value.")
            
            elif choice == '4':
                break
            else:
                print("Invalid choice. Please enter 1-4.")
    
    except Exception as e:
        print(f"Error managing phone numbers: {e}")
    finally:
        if conn:
            conn.close()