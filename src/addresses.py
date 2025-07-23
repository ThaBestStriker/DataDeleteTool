import sqlite3
import sqlcipher3
import os
import signal

def signal_handler(sig, frame):
    """Handle Ctrl+S to skip input."""
    raise KeyboardInterrupt

def modify_addresses(passphrase, user_id):
    """Modify address information for a specific user_id."""
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
            print("\nAddress Options:")
            print("1: Add new address")
            print("2: View existing addresses")
            print("3: Delete address")
            print("4: Back to modify user menu")
            choice = input("Enter choice (1-4): ").strip()
            
            if choice == '1':
                signal.signal(signal.SIGTSTP, signal_handler)
                street = None
                city = None
                state = None
                zip_code = None
                is_current = None
                try:
                    street = input("Street: ").strip() or None
                except KeyboardInterrupt:
                    street = None
                try:
                    city = input("City: ").strip() or None
                except KeyboardInterrupt:
                    city = None
                try:
                    state = input("State (e.g., CA): ").strip() or None
                except KeyboardInterrupt:
                    state = None
                try:
                    zip_code = input("ZIP: ").strip() or None
                except KeyboardInterrupt:
                    zip_code = None
                try:
                    is_current_input = input("Is current address (y/N)? ").strip().lower()
                    is_current = 1 if is_current_input == 'y' else 0
                except KeyboardInterrupt:
                    is_current = 0
                signal.signal(signal.SIGTSTP, signal.SIG_DFL)
                
                if not street or not city or not state or not zip_code:
                    print("All address fields (street, city, state, ZIP) are required.")
                    continue
                
                cursor.execute("""
                INSERT INTO addresses (user_id, street, city, state, zip, is_current)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, street, city, state, zip_code, is_current))
                conn.commit()
                print("Address added.")
            
            elif choice == '2':
                cursor.execute("SELECT address_id, street, city, state, zip, is_current FROM addresses WHERE user_id = ?", (user_id,))
                addresses = cursor.fetchall()
                if not addresses:
                    print("No addresses found for this user.")
                else:
                    print("\nAddresses:")
                    for addr in addresses:
                        address_id, street, city, state, zip_code, is_current = addr
                        print(f"Address ID: {address_id}")
                        print(f"Street: {street}")
                        print(f"City: {city}")
                        print(f"State: {state}")
                        print(f"ZIP: {zip_code}")
                        print(f"Current: {'Yes' if is_current else 'No'}")
                        print()
            
            elif choice == '3':
                cursor.execute("SELECT address_id, street, city FROM addresses WHERE user_id = ?", (user_id,))
                addresses = cursor.fetchall()
                if not addresses:
                    print("No addresses found for this user.")
                    continue
                print("\nAddresses:")
                for addr in addresses:
                    address_id, street, city = addr
                    print(f"Address ID: {address_id}, {street}, {city}")
                try:
                    address_id = int(input("Enter address_id to delete: ").strip())
                    cursor.execute("SELECT 1 FROM addresses WHERE address_id = ? AND user_id = ?", (address_id, user_id))
                    if not cursor.fetchone():
                        print(f"No address found with address_id {address_id} for this user.")
                        continue
                    cursor.execute("DELETE FROM addresses WHERE address_id = ?", (address_id,))
                    conn.commit()
                    print(f"Address ID {address_id} deleted.")
                except ValueError:
                    print("Invalid address_id. Please enter a numeric value.")
            
            elif choice == '4':
                break
            else:
                print("Invalid choice. Please enter 1-4.")
    
    except Exception as e:
        print(f"Error managing addresses: {e}")
    finally:
        if conn:
            conn.close()