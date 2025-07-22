#!/usr/bin/env python3
import getpass  # For masked password input
import os
import sys
import datetime
import sqlite3  # For unencrypted DB checks and unencrypted init
import signal  # For Ctrl+C trap
import logging  # For debug logging
import shutil  # For DB copy in backups
from src.main import DataDeleteConsole  # Import the CLI class
import sqlcipher3  # For encrypted operations (rekey)

# Ctrl+C handler
def signal_handler(sig, frame):
    print("ctrl+c detected; attempting to close GHOSTWIPE gracefully.")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Clear screen at launch for clean UI
os.system('clear')

# Setup debug logging if --debug flag (file-only, no console)
if '--debug' in sys.argv:
    debug_dir = os.path.join('data', 'debug')
    os.makedirs(debug_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S")
    log_file = os.path.join(debug_dir, f"{timestamp} DebugLog")
    logging.basicConfig(filename=log_file, level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
    logging.debug("Developer mode enabled. Logging started.")

class Tee(object):
    """Redirect stdout/stderr to logger if debug mode (skip empty lines)."""
    def __init__(self, stream):
        self.stream = stream

    def write(self, data):
        stripped = data.strip()
        if stripped and '--debug' in sys.argv:
            logging.debug(stripped)
        self.stream.write(data)
        self.stream.flush()

    def flush(self):
        self.stream.flush()

if '--debug' in sys.argv:
    sys.stdout = Tee(sys.stdout)
    sys.stderr = Tee(sys.stderr)

def log_debug(message):
    if '--debug' in sys.argv:
        logging.debug(message)

def log_input(prompt, input_value):
    if '--debug' in sys.argv:
        logging.debug(f"User input for '{prompt}': {input_value}")

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
        log_debug("Database encrypted successfully.")
    except sqlcipher3.Error as e:
        log_debug(f"Encryption error: {e}")
        raise
    finally:
        conn.close()

def make_backup(db_path, base_backup_name='pii_data.db.bak'):
    """Make a rotating backup, prompting for overwrite if base exists."""
    today = datetime.datetime.now().strftime("%y%m%d")
    base_backup_filename = f"{today}.{base_backup_name}"
    base_backup_path = os.path.join('data', base_backup_filename)

    if os.path.exists(base_backup_path):
        overwrite = input("Overwrite existing backup? (y/N): ").lower()
        log_input("Overwrite existing backup? (y/N): ", overwrite)
        if overwrite == '' or overwrite == 'n':
            # Preserve with rotating numbers (lowest most recent)
            i = 1
            while True:
                rot_backup_filename = f"{today}.{base_backup_name}.{i}"
                rot_backup_path = os.path.join('data', rot_backup_filename)
                if not os.path.exists(rot_backup_path):
                    break
                i += 1
            # Shift existing backups up
            j = i
            while j > 1:
                prev_rot = os.path.join('data', f"{today}.{base_backup_name}.{j-1}")
                curr_rot = os.path.join('data', f"{today}.{base_backup_name}.{j}")
                os.rename(prev_rot, curr_rot)
                j -= 1
            # Rename base to .2 if i>1
            if i > 1:
                os.rename(base_backup_path, os.path.join('data', f"{today}.{base_backup_name}.2"))
            # New backup as .1
            backup_path = os.path.join('data', f"{today}.{base_backup_name}.1")
        else:
            # Overwrite base
            backup_path = base_backup_path
    else:
        backup_path = base_backup_path

    shutil.copy(db_path, backup_path)  # Copy for option 1 preservation
    print(f"Backed up old DB to full path: {os.path.abspath(backup_path)}.")
    log_debug(f"Backed up DB to {os.path.abspath(backup_path)}.")
    return backup_path

def backup_and_create_new(db_path):
    """Backup old DB and prompt for new encrypted one."""
    backup_path = make_backup(db_path)
    while True:
        passphrase = getpass.getpass("Enter a strong password for new DB: ")
        confirm_passphrase = getpass.getpass("Confirm password: ")
        log_input("Enter a strong password for new DB: ", "[masked]")
        log_input("Confirm password: ", "[masked]")
        if passphrase == confirm_passphrase:
            # Ensure no residual file
            if os.path.exists(db_path):
                os.remove(db_path)
                log_debug(f"Removed residual file at {db_path} before new creation.")
            return passphrase
        print("Passwords do not match.")
        retry = input("Try again? (Y/n): ").lower()
        log_input("Try again? (Y/n): ", retry)
        if retry == 'n':
            os.system('clear')  # Clear screen before revert message
            os.rename(backup_path, db_path)
            print(f"Reverting database file to {os.path.abspath(db_path)}")
            print()  # Newline for readability
            return None  # Return to menu
        # Default to Y on enter or other inputs

def unencrypt_db(db_path):
    """Hidden dev command: Backup, create new unencrypted DB, proceed without password."""
    if os.path.exists(db_path):
        make_backup(db_path)
    # Create new unencrypted DB
    conn = sqlite3.connect(db_path)
    try:
        # Run schema creation without encryption (copy from init_db but use sqlite3)
        # Users table
        conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            primary_email TEXT,
            primary_phone TEXT,
            state TEXT  -- For privacy law tracking (e.g., CA for CCPA)
        )
        ''')
        # Addresses table
        conn.execute('''
        CREATE TABLE IF NOT EXISTS addresses (
            address_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            street TEXT,
            city TEXT,
            state TEXT,
            zip TEXT,
            is_current BOOLEAN,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        # Emails table
        conn.execute('''
        CREATE TABLE IF NOT EXISTS emails (
            email_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            email_address TEXT,
            source_site TEXT,
            is_active BOOLEAN,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        # Usernames table
        conn.execute('''
        CREATE TABLE IF NOT EXISTS usernames (
            username_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            platform TEXT,
            is_tied BOOLEAN,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        # Broker sites table
        conn.execute('''
        CREATE TABLE IF NOT EXISTS broker_sites (
            site_id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT,
            name TEXT,
            last_updated TEXT,
            deletion_url TEXT
        )
        ''')
        # Opt-out requests table
        conn.execute('''
        CREATE TABLE IF NOT EXISTS opt_out_requests (
            request_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            site_id INTEGER,
            status TEXT,  -- pending, resolved
            request_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (site_id) REFERENCES broker_sites (site_id)
        )
        ''')
        conn.commit()
        print("New unencrypted DB created for dev mode.")
        log_debug("New unencrypted DB created for dev mode.")
    finally:
        conn.close()
    return ''  # Proceed without password

def handle_encryption_error(e):
    print(f"Encryption error: {e}")
    log_debug(f"Encryption error: {e}")
    print("Debug information: Check if the DB is already encrypted or if passphrase is valid.")
    print("Returning to main menu.")

if __name__ == "__main__":
    db_path = os.path.join('data', 'pii_data.db')
    if not os.path.exists(db_path):
        print("First-time setup: No database found.")
        encrypt_choice = input("Would you like to encrypt the database? (y/n): ").lower()
        log_input("Would you like to encrypt the database? (y/n): ", encrypt_choice)
        if encrypt_choice == 'y':
            passphrase = getpass.getpass("Enter a strong password: ")
            confirm_passphrase = getpass.getpass("Confirm password: ")
            log_input("Enter a strong password: ", "[masked]")
            log_input("Confirm password: ", "[masked]")
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
                choice = input("Enter choice (1/2/3): ").strip().lower()
                log_input("Enter choice (1/2/3): ", choice)
                if choice == 'unencrypt_db':
                    passphrase = unencrypt_db(db_path)  # Proceed without password
                    break
                elif choice == '1':
                    # Backup before encryption (copy, not move)
                    make_backup(db_path, 'pre_encrypt.bak')
                    passphrase = getpass.getpass("Enter a strong password: ")
                    confirm_passphrase = getpass.getpass("Confirm password: ")
                    log_input("Enter a strong password: ", "[masked]")
                    log_input("Confirm password: ", "[masked]")
                    if passphrase != confirm_passphrase:
                        print("Passwords do not match. Exiting.")
                        sys.exit(1)
                    try:
                        encrypt_existing_db(db_path, passphrase)
                    except sqlcipher3.Error as e:
                        handle_encryption_error(e)
                        continue  # Return to menu on error
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
            log_input("Enter database password: ", "[masked]")

    # Launch console with passphrase (will verify in init_db)
    try:
        DataDeleteConsole(passphrase).cmdloop()
    except Exception as e:  # Catch general errors (e.g., invalid passphrase)
        print(f"Error: {e}. Exiting.")
        sys.exit(1)