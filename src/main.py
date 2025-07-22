import cmd
import sqlite3
import os
import sys
# Add project root to sys.path for imports (robust for root launcher)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.db import init_db  # Import DB init

class DataDeleteConsole(cmd.Cmd):
    intro = 'Welcome to GHOSTWIPE (GHWI). Type help or ? for commands. Type quit to exit.\n'
    prompt = '(GHWI) '

    def __init__(self):
        super().__init__()
        init_db()  # Ensure DB is initialized
        self.conn = sqlite3.connect(os.path.join('data', 'pii_data.db'))
        self.cursor = self.conn.cursor()
        self.show_menu()

    def show_menu(self):
        print("\nMenu Options:")
        print("1: user_info - Populate or modify user PII")
        print("2: database - Manage broker sites and opt-out links")
        print("3: scan - Scan data brokers for PII")
        print("Type a number (1-3) or command name (partial + tab to autocomplete).")

    def precmd(self, line):
        # Map numbers to commands
        if line == '1':
            return 'user_info'
        elif line == '2':
            return 'database'
        elif line == '3':
            return 'scan'
        return line

    def do_user_info(self, arg):
        """Populate or modify user PII in the database."""
        # Example prompts; expand with full PII fields
        first_name = input("Enter first name: ")
        last_name = input("Enter last name: ")
        state = input("Enter state (e.g., CA): ")
        # Insert example (expand for addresses, emails, etc.)
        self.cursor.execute("INSERT INTO users (first_name, last_name, state) VALUES (?, ?, ?)",
                            (first_name, last_name, state))
        self.conn.commit()
        print("User info added/updated.")
        self.show_menu()

    def do_database(self, arg):
        """Manage broker sites and opt-out links."""
        # Example: Add a broker site
        name = input("Enter broker name: ")
        url = input("Enter broker URL: ")
        deletion_url = input("Enter deletion URL: ")
        self.cursor.execute("INSERT INTO broker_sites (name, url, deletion_url) VALUES (?, ?, ?)",
                            (name, url, deletion_url))
        self.conn.commit()
        print("Broker site added.")
        # TODO: Add view/edit opt-out requests
        self.show_menu()

    def do_scan(self, arg):
        """Scan data brokers for PII (placeholder)."""
        print("Scanning feature not implemented yet.")
        self.show_menu()

    def do_quit(self, arg):
        """Exit the tool."""
        print("Exiting GHOSTWIPE.")
        self.conn.close()
        return True

    # Completer for all commands (supports partial + tab)
    def complete(self, text, state):
        options = ['user_info', 'database', 'scan', 'quit']
        matches = [opt for opt in options if opt.startswith(text)]
        if state < len(matches):
            return matches[state]
        else:
            return None

    def default(self, line):
        print(f"Unknown command: {line}. Type help or ? for options.")
        self.show_menu()

if __name__ == "__main__":
    DataDeleteConsole().cmdloop()
