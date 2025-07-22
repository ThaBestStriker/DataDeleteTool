#!/usr/bin/env python3
import getpass  # For masked password input
import os
import sys
import datetime
import sqlite3  # For unencrypted DB checks
from src.main import DataDeleteConsole  # Import the CLI class
import sqlcipher3  # For encrypted operations (rekey)

def is_db_encrypted(db_path):
    """Check if DB is encrypted by trying to open without key."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        conn.close()
        # If query succeeds and finds expected tables, it's unencrypted
        if any('users' in table for table in tables):
            return False
        return True  # Encrypted if query fails or no tables
    except sqlite3.Error:
        return True  # Encrypted if access fails without key

def encrypt_existing_db(db_path, passphrase):
    """Encrypt an existing unencrypted DB using rekey."""
    conn = sqlcipher3.connect(db_path)
    try:
        conn.execute(f"PRAGMA rekey = '{passphrase}'")  # Encrypt with new key
        conn.execute("PRAGMA kdf_iter = 640000")  # Set high iterations
        conn.commit()
        print("Database encrypted successfully.")
    except sqlcipher3.Error as e:
        print(f"Encryption error: {e}")
        sys.exit(1)
    finally:
        conn.close()

def backup_and_create_new(db_path):
    """Backup old DB and prompt for new encrypted one."""
    today = datetime.datetime.now().strftime("%y%m%d")
    backup_filename = f"{today}.pii_data.db.bak"
    backup_path = os.path.join('data', backup_filename)
    os.rename(db_path, backup_path)
    print(f"Backed up old DB to full path: {os.path.abspath(backup_path)}.")

    while True:
        passphrase = getpass.getpass("Enter a strong password for new DB: ")
        confirm_passphrase = getpass.getpass("Confirm password: ")
        if passphrase == confirm_passphrase:
            return passphrase
        print("Passwords do not match.")
        retry = input("Try again? (Y/n): ").lower()
        if retry == 'n':
            # Revert rename on "n"
            os.system('clear')  # Clear screen before revert message
            os.rename(backup_path, db_path)
            print(f"Reverting database file to {os.path.abspath(db_path)}")
            print()  # Newline for readability
            return None  # Return to menu
        # Default to Y on enter or other inputs

if __name__ == "__main__":
    db_path = os.path.join('data', 'pii_data.db')
    if not os.path.exists(db_path):
        print("First-time setup: No database found.")
        encrypt_choice = input("Would you like to encrypt the database? (y/n): ").lower()
        if encrypt_choice == 'y':
            passphrase = getpass.getpass("Enter a strong password: ")
            confirm_passphrase = getpass.getpass("Confirm password: ")
            if passphrase != confirm_passphrase:
                print("Passwords do not match. Exiting.")
                sys.exit(1)
        else:
            print("Database will not be encrypted. Exiting for security reasons.")
            sys.exit(1)
    else:
        if not is_db_encrypted(db_path):
            print("Existing database is unencrypted.")
            while True:
                print("Options:")
                print("1: Encrypt the database")
                print("2: Create a new database")
                print("3: Close GHOSTWIPE Launcher")
                choice = input("Enter choice (1/2/3): ")
                if choice == '1':
                    passphrase = getpass.getpass("Enter a strong password: ")
                    confirm_passphrase = getpass.getpass("Confirm password: ")
                    if passphrase != confirm_passphrase:
                        print("Passwords do not match. Exiting.")
                        sys.exit(1)
                    encrypt_existing_db(db_path, passphrase)
                    break
                elif choice == '2':
                    passphrase = backup_and_create_new(db_path)
                    if passphrase is None:
                        continue  # Return to menu after revert
                    break
                elif choice == '3':
                    print("Closing GHOSTWIPE.")
                    sys.exit(0)
                else:
                    print("Invalid choice. Try again.")
        else:
            passphrase = getpass.getpass("Enter database password: ")

    # Launch console with passphrase (will verify in init_db)
    try:
        DataDeleteConsole(passphrase).cmdloop()
    except Exception as e:  # Catch general errors (e.g., invalid passphrase)
        print(f"Error: {e}. Exiting.")
        sys.exit(1)