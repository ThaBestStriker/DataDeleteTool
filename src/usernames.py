import sqlite3
import sqlcipher3
import os
import signal

def signal_handler(sig, frame):
    """Handle Ctrl+S to skip input."""
    raise KeyboardInterrupt

def modify_usernames(passphrase, user_id):
    """Modify username information for a specific user_id."""
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
            print("\nUsername Options:")
            print("1: Add new username")
            print("2: View existing usernames")
            print("3: Delete username")
            print("4: Back to modify user menu")
            choice = input("Enter choice (1-4): ").strip()
            
            if choice == '1':
                signal.signal(signal.SIGTSTP, signal_handler)
                username = None
                platform = None
                is_tied = None
                try:
                    username = input("Username: ").strip() or None
                except KeyboardInterrupt:
                    username = None
                try:
                    platform = input("Platform (e.g., Twitter): ").strip() or None
                except KeyboardInterrupt:
                    platform = None
                try:
                    is_tied_input = input("Is tied to user (y/N)? ").strip().lower()
                    is_tied = 1 if is_tied_input == 'y' else 0
                except KeyboardInterrupt:
                    is_tied = 0
                signal.signal(signal.SIGTSTP, signal.SIG_DFL)
                
                if not username or not platform:
                    print("Username and platform are required.")
                    continue
                
                cursor.execute("""
                INSERT INTO usernames (user_id, username, platform, is_tied)
                VALUES (?, ?, ?, ?)
                """, (user_id, username, platform, is_tied))
                conn.commit()
                print("Username added.")
            
            elif choice == '2':
                cursor.execute("SELECT username_id, username, platform, is_tied FROM usernames WHERE user_id = ?", (user_id,))
                usernames = cursor.fetchall()
                if not usernames:
                    print("No usernames found for this user.")
                else:
                    print("\nUsernames:")
                    for uname in usernames:
                        username_id, username, platform, is_tied = uname
                        print(f"Username ID: {username_id}")
                        print(f"Username: {username}")
                        print(f"Platform: {platform}")
                        print(f"Tied: {'Yes' if is_tied else 'No'}")
                        print()
            
            elif choice == '3':
                cursor.execute("SELECT username_id, username, platform FROM usernames WHERE user_id = ?", (user_id,))
                usernames = cursor.fetchall()
                if not usernames:
                    print("No usernames found for this user.")
                    continue
                print("\nUsernames:")
                for uname in usernames:
                    username_id, username, platform = uname
                    print(f"Username ID: {username_id}, {username} ({platform})")
                try:
                    username_id = int(input("Enter username_id to delete: ").strip())
                    cursor.execute("SELECT 1 FROM usernames WHERE username_id = ? AND user_id = ?", (username_id, user_id))
                    if not cursor.fetchone():
                        print(f"No username found with username_id {username_id} for this user.")
                        continue
                    cursor.execute("DELETE FROM usernames WHERE username_id = ?", (username_id,))
                    conn.commit()
                    print(f"Username ID {username_id} deleted.")
                except ValueError:
                    print("Invalid username_id. Please enter a numeric value.")
            
            elif choice == '4':
                break
            else:
                print("Invalid choice. Please enter 1-4.")
    
    except Exception as e:
        print(f"Error managing usernames: {e}")
    finally:
        if conn:
            conn.close()