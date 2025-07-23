import sqlite3
import sqlcipher3
import os
import signal

def signal_handler(sig, frame):
    """Handle Ctrl+S to skip input."""
    raise KeyboardInterrupt

def userinfo(passphrase):
    """Manage user information in the GHOSTWIPE database."""
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
            print("\nUser Info Options:")
            print("1: Add new name")
            print("2: Modify existing user information")
            print("3: Delete user information")
            print("4: Back to main menu")
            choice = input("Enter choice (1-4): ").strip()
            
            if choice == '1':
                while True:
                    print("\nEnter user details (Ctrl+S to skip optional fields):")
                    signal.signal(signal.SIGTSTP, signal_handler)  # Catch Ctrl+S
                    first_name = None
                    middle_name = None
                    last_name = None
                    try:
                        first_name = input("First Name: ").strip() or None
                    except KeyboardInterrupt:
                        first_name = None
                    try:
                        middle_name = input("Middle Name (optional): ").strip() or None
                    except KeyboardInterrupt:
                        middle_name = None
                    try:
                        last_name = input("Last Name: ").strip() or None
                    except KeyboardInterrupt:
                        last_name = None
                    signal.signal(signal.SIGTSTP, signal.SIG_DFL)  # Reset Ctrl+S handler
                    
                    if not first_name and not last_name:
                        print("At least one of First Name or Last Name is required.")
                        continue
                    
                    cursor.execute("""
                    INSERT INTO users (first_name, middle_name, last_name)
                    VALUES (?, ?, ?)
                    """, (first_name, middle_name, last_name))
                    conn.commit()
                    user_id = cursor.lastrowid
                    print(f"User added with user_id: {user_id}")
                    
                    add_another = input("Would you like to add another user (y/N)? ").strip().lower()
                    if add_another != 'y':
                        break
            
            elif choice == '2':
                cursor.execute("SELECT user_id, first_name, last_name FROM users")
                users = cursor.fetchall()
                if not users:
                    print("No users found in the database.")
                    continue
                print("\nExisting Users:")
                for user in users:
                    user_id, first_name, last_name = user
                    name = f"{first_name or ''} {last_name or ''}".strip()
                    print(f"User ID: {user_id}, Name: {name}")
                
                try:
                    user_id = int(input("Enter user_id to modify: ").strip())
                    cursor.execute("SELECT first_name, last_name FROM users WHERE user_id = ?", (user_id,))
                    user = cursor.fetchone()
                    if not user:
                        print(f"No user found with user_id {user_id}.")
                        continue
                    first_name, last_name = user
                    print(f"\nModifying user: {first_name or ''} {last_name or ''}")
                    
                    from src.names import modify_names
                    from src.addresses import modify_addresses
                    from src.emails import modify_emails
                    from src.phone_numbers import modify_phone_numbers
                    from src.usernames import modify_usernames
                    
                    while True:
                        print("\nModify User Options:")
                        print("1: Display All User Info")
                        print("2: Names")
                        print("3: Addresses")
                        print("4: Emails")
                        print("5: Phone Numbers")
                        print("6: Usernames")
                        print("D: Delete User")
                        print("b: Go back to previous menu")
                        sub_choice = input("Enter choice (1-6, D, b): ").strip().lower()
                        
                        if sub_choice == '1':
                            print(f"\nUser Information for {first_name or ''} {last_name or ''} (User ID: {user_id}):")
                            
                            # Users table
                            cursor.execute("""
                            SELECT first_name, middle_name, last_name, primary_email, primary_phone, state
                            FROM users WHERE user_id = ?
                            """, (user_id,))
                            user_info = cursor.fetchone()
                            print("\nBasic Info:")
                            print(f"First Name: {user_info[0] or 'None'}")
                            print(f"Middle Name: {user_info[1] or 'None'}")
                            print(f"Last Name: {user_info[2] or 'None'}")
                            print(f"Primary Email: {user_info[3] or 'None'}")
                            print(f"Primary Phone: {user_info[4] or 'None'}")
                            print(f"State: {user_info[5] or 'None'}")
                            
                            # Addresses table
                            cursor.execute("""
                            SELECT address_id, street, city, state, zip, is_current
                            FROM addresses WHERE user_id = ?
                            """, (user_id,))
                            addresses = cursor.fetchall()
                            print("\nAddresses:")
                            if not addresses:
                                print("No addresses found.")
                            for addr in addresses:
                                print(f"Address ID: {addr[0]}")
                                print(f"Street: {addr[1] or 'None'}")
                                print(f"City: {addr[2] or 'None'}")
                                print(f"State: {addr[3] or 'None'}")
                                print(f"ZIP: {addr[4] or 'None'}")
                                print(f"Current: {'Yes' if addr[5] else 'No'}")
                                print()
                            
                            # Emails table
                            cursor.execute("""
                            SELECT email_id, email_address, source_site, is_active
                            FROM emails WHERE user_id = ?
                            """, (user_id,))
                            emails = cursor.fetchall()
                            print("Emails:")
                            if not emails:
                                print("No emails found.")
                            for email in emails:
                                print(f"Email ID: {email[0]}")
                                print(f"Email Address: {email[1] or 'None'}")
                                print(f"Source Site: {email[2] or 'None'}")
                                print(f"Active: {'Yes' if email[3] else 'No'}")
                                print()
                            
                            # Phone Numbers table
                            cursor.execute("""
                            SELECT phone_id, phone_number, source_site, is_active
                            FROM phone_numbers WHERE user_id = ?
                            """, (user_id,))
                            phones = cursor.fetchall()
                            print("Phone Numbers:")
                            if not phones:
                                print("No phone numbers found.")
                            for phone in phones:
                                print(f"Phone ID: {phone[0]}")
                                print(f"Phone Number: {phone[1] or 'None'}")
                                print(f"Source Site: {phone[2] or 'None'}")
                                print(f"Active: {'Yes' if phone[3] else 'No'}")
                                print()
                            
                            # Usernames table
                            cursor.execute("""
                            SELECT username_id, username, platform, is_tied
                            FROM usernames WHERE user_id = ?
                            """, (user_id,))
                            usernames = cursor.fetchall()
                            print("Usernames:")
                            if not usernames:
                                print("No usernames found.")
                            for uname in usernames:
                                print(f"Username ID: {uname[0]}")
                                print(f"Username: {uname[1] or 'None'}")
                                print(f"Platform: {uname[2] or 'None'}")
                                print(f"Tied: {'Yes' if uname[3] else 'No'}")
                                print()
                            
                            # Opt-out Requests
                            cursor.execute("""
                            SELECT oor.request_id, bs.name, oor.status, oor.request_date
                            FROM opt_out_requests oor
                            JOIN broker_sites bs ON oor.site_id = bs.site_id
                            WHERE oor.user_id = ?
                            """, (user_id,))
                            requests = cursor.fetchall()
                            print("Opt-out Requests:")
                            if not requests:
                                print("No opt-out requests found.")
                            for req in requests:
                                print(f"Request ID: {req[0]}")
                                print(f"Broker Site: {req[1]}")
                                print(f"Status: {req[2] or 'None'}")
                                print(f"Request Date: {req[3] or 'None'}")
                                print()
                            
                            # Cleaning Records (via broker_sites)
                            cursor.execute("""
                            SELECT cr.record_id, cr.site_name, cr.date_cleaned, cr.date_confirmed_deleted
                            FROM cleaning_records cr
                            JOIN broker_sites bs ON cr.site_id = bs.site_id
                            WHERE cr.site_id IN (SELECT site_id FROM opt_out_requests WHERE user_id = ?)
                            """, (user_id,))
                            cleaning_records = cursor.fetchall()
                            print("Cleaning Records:")
                            if not cleaning_records:
                                print("No cleaning records found.")
                            for record in cleaning_records:
                                print(f"Record ID: {record[0]}")
                                print(f"Site Name: {record[1]}")
                                print(f"Date Cleaned: {record[2] or 'None'}")
                                print(f"Date Confirmed Deleted: {record[3] or 'None'}")
                                print()
                        
                        elif sub_choice == '2':
                            modify_names(passphrase, user_id)
                        elif sub_choice == '3':
                            modify_addresses(passphrase, user_id)
                        elif sub_choice == '4':
                            modify_emails(passphrase, user_id)
                        elif sub_choice == '5':
                            modify_phone_numbers(passphrase, user_id)
                        elif sub_choice == '6':
                            modify_usernames(passphrase, user_id)
                        elif sub_choice == 'd':
                            name = f"{first_name or ''} {last_name or ''}".strip()
                            confirmation = input(f"Are you sure you want to Delete {name} from the database? Type 'DELETE': ").strip()
                            if confirmation == 'DELETE':
                                # Delete associated records
                                cursor.execute("DELETE FROM addresses WHERE user_id = ?", (user_id,))
                                cursor.execute("DELETE FROM emails WHERE user_id = ?", (user_id,))
                                cursor.execute("DELETE FROM phone_numbers WHERE user_id = ?", (user_id,))
                                cursor.execute("DELETE FROM usernames WHERE user_id = ?", (user_id,))
                                cursor.execute("DELETE FROM opt_out_requests WHERE user_id = ?", (user_id,))
                                cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
                                conn.commit()
                                print(f"User {name} (user_id: {user_id}) and associated records deleted.")
                                break
                            else:
                                print("Deletion cancelled. Confirmation must be exactly 'DELETE'.")
                        elif sub_choice == 'b':
                            break
                        else:
                            print("Invalid choice. Please enter 1-6, D, or b.")
                except ValueError:
                    print("Invalid user_id. Please enter a numeric value.")
            
            elif choice == '3':
                cursor.execute("SELECT user_id, first_name, last_name FROM users")
                users = cursor.fetchall()
                if not users:
                    print("No users found in the database.")
                    continue
                print("\nExisting Users:")
                for user in users:
                    user_id, first_name, last_name = user
                    name = f"{first_name or ''} {last_name or ''}".strip()
                    print(f"User ID: {user_id}, Name: {name}")
                
                try:
                    user_id = int(input("Enter user_id to delete: ").strip())
                    cursor.execute("SELECT first_name, last_name FROM users WHERE user_id = ?", (user_id,))
                    user = cursor.fetchone()
                    if not user:
                        print(f"No user found with user_id {user_id}.")
                        continue
                    first_name, last_name = user
                    name = f"{first_name or ''} {last_name or ''}".strip()
                    confirmation = input(f"Are you sure you want to Delete {name} from the database? Type 'DELETE': ").strip()
                    if confirmation == 'DELETE':
                        cursor.execute("DELETE FROM addresses WHERE user_id = ?", (user_id,))
                        cursor.execute("DELETE FROM emails WHERE user_id = ?", (user_id,))
                        cursor.execute("DELETE FROM phone_numbers WHERE user_id = ?", (user_id,))
                        cursor.execute("DELETE FROM usernames WHERE user_id = ?", (user_id,))
                        cursor.execute("DELETE FROM opt_out_requests WHERE user_id = ?", (user_id,))
                        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
                        conn.commit()
                        print(f"User {name} (user_id: {user_id}) and associated records deleted.")
                    else:
                        print("Deletion cancelled. Confirmation must be exactly 'DELETE'.")
                except ValueError:
                    print("Invalid user_id. Please enter a numeric value.")
            
            elif choice == '4':
                break
            else:
                print("Invalid choice. Please enter 1-4.")
    
    except Exception as e:
        print(f"Error managing user info: {e}")
    finally:
        if conn:
            conn.close()