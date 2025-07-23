import cmd
import getpass
import os
import sys
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.db import init_db
import sqlite3
import sqlcipher3
import gnureadline as readline
readline.parse_and_bind("tab: complete")
from src.view_db import view_db
from src.cleaning import cleaning
from src.userinfo import userinfo

class DataDeleteConsole(cmd.Cmd):
    intro = 'Welcome to GHOSTWIPE (GHWI). Type help or ? for commands. Type quit to exit.\n'
    prompt = '(GHWI) '

    def __init__(self, passphrase):
        super().__init__()
        self.passphrase = passphrase
        init_db(self.passphrase)
        if self.passphrase:
            self.conn = sqlcipher3.connect(os.path.join('data', 'pii_data.db'))
            self.conn.execute(f"PRAGMA key = '{self.passphrase}'")
            self.conn.execute("PRAGMA kdf_iter = 64000")
            self.conn.execute("PRAGMA cipher_page_size = 4096")
        else:
            self.conn = sqlite3.connect(os.path.join('data', 'pii_data.db'))
        self.cursor = self.conn.cursor()
        self.show_menu()

    def show_menu(self):
        print("\nMenu Options:")
        print("1: user_info - Populate or modify user PII")
        print("2: database - Manage broker sites and opt-out links")
        print("3: scan - Scan data brokers for PII")
        print("4: start_cleaning - Manage data broker cleaning requests")
        print("Type a number (1-4) or command name (partial + tab to autocomplete).")

    def precmd(self, line):
        if line == '1':
            return 'user_info'
        elif line == '2':
            return 'database'
        elif line == '3':
            return 'scan'
        elif line == '4':
            return 'start_cleaning'
        return line

    def do_user_info(self, arg):
        """Populate or modify user PII in the database."""
        userinfo(self.passphrase)
        self.show_menu()

    def do_database(self, arg):
        """Manage broker sites and opt-out links."""
        while True:
            print("\nDatabase Options:")
            print("1: View entries")
            print("2: Delete entries (not implemented)")
            print("3: Modify entries (not implemented)")
            print("4: Add entries (manual)")
            print("5: Back to main menu")
            choice = input("Enter choice (1-5): ").strip()
            
            if choice == '1':
                view_db(self.passphrase)
            elif choice == '2':
                print("Delete entries not implemented yet.")
            elif choice == '3':
                print("Modify entries not implemented yet.")
            elif choice == '4':
                name = input("Enter broker name: ")
                url = input("Enter broker URL: ")
                deletion_url = input("Enter deletion URL: ")
                privacy_policy = input("Enter privacy policy URL (optional): ")
                contact = input("Enter contact info (optional): ")
                requirements = input("Enter requirements (optional): ")
                notes = input("Enter notes (optional): ")
                last_updated = datetime.date.today().isoformat()
                self.cursor.execute("""
                INSERT INTO broker_sites (name, url, deletion_url, privacy_policy, contact, requirements, notes, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (name, url, deletion_url, privacy_policy or None, contact or None, requirements or None, notes or None, last_updated))
                self.conn.commit()
                print("Broker site added.")
            elif choice == '5':
                break
            else:
                print("Invalid choice. Please enter 1-5.")
        self.show_menu()

    def do_scan(self, arg):
        """Scan data brokers for PII (placeholder)."""
        print("Scanning feature not implemented yet.")
        self.show_menu()

    def do_start_cleaning(self, arg):
        """Manage data broker cleaning requests."""
        cleaning(self.passphrase)
        self.show_menu()

    def do_quit(self, arg):
        """Exit the tool."""
        print("Exiting GHOSTWIPE.")
        self.conn.close()
        return True

    def complete(self, text, state):
        options = ['user_info', 'database', 'scan', 'start_cleaning', 'quit']
        matches = [opt for opt in options if opt.startswith(text)]
        if state < len(matches):
            return matches[state]
        else:
            return None

    def default(self, line):
        print(f"Unknown command: {line}. Type help or ? for options.")
        self.show_menu()

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
        passphrase = getpass.getpass("Enter database password: ")

    try:
        DataDeleteConsole(passphrase).cmdloop()
    except Exception as e:
        print(f"Error: {e}. Exiting.")
        sys.exit(1)