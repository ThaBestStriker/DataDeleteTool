import sqlite3
import sqlcipher3
import os
import signal

def signal_handler(sig, frame):
    """Handle Ctrl+S to skip input."""
    raise KeyboardInterrupt

def modify_names(passphrase, user_id):
    """Modify name information for a specific user_id."""
    db_path = os.path.join('data', 'pii_data.db')
    conn = None
    try:
        conn = sqlcipher3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA key = '{passphrase}'")
        cursor.execute("PRAGMA kdf_iter = 64000")
        cursor.execute("PRAGMA cipher_page_size = 4096")
        cursor.execute("PRAGMA foreign_keys = ON")
        
        cursor.execute("SELECT first_name, last_name FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            print(f"No user found with user_id {user_id}.")
            return
        
        first_name, last_name = user
        print(f"\nCurrent Name: {first_name or ''} {last_name or ''}")
        print("Enter new details (Ctrl+S to skip, leave blank to keep current):")
        
        signal.signal(signal.SIGTSTP, signal_handler)
        new_first_name = None
        new_middle_name = None
        new_last_name = None
        try:
            new_first_name = input(f"First Name [{first_name or ''}]: ").strip() or first_name
        except KeyboardInterrupt:
            new_first_name = first_name
        try:
            new_middle_name = input("Middle Name (optional): ").strip() or None
        except KeyboardInterrupt:
            new_middle_name = None
        try:
            new_last_name = input(f"Last Name [{last_name or ''}]: ").strip() or last_name
        except KeyboardInterrupt:
            new_last_name = last_name
        signal.signal(signal.SIGTSTP, signal.SIG_DFL)
        
        if not new_first_name and not new_last_name:
            print("At least one of First Name or Last Name is required.")
            return
        
        cursor.execute("""
        UPDATE users
        SET first_name = ?, middle_name = ?, last_name = ?
        WHERE user_id = ?
        """, (new_first_name, new_middle_name, new_last_name, user_id))
        conn.commit()
        print(f"Name updated for user_id {user_id}.")
    
    except Exception as e:
        print(f"Error modifying names: {e}")
    finally:
        if conn:
            conn.close()