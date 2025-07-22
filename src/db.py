import sqlite3
import os

def init_db():
    """Initialize SQLite database for DataDeleteTool."""
    db_path = os.path.join('data', 'pii_data.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
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
    cursor.execute('''
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
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS emails (
        email_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        email_address TEXT,
        source_site TEXT,
        is_active BOOLEAN,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')

    # Usernames table (for social media accounts)
    cursor.execute('''
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
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS broker_sites (
        site_id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT,
        name TEXT,
        last_updated TEXT,
        deletion_url TEXT
    )
    ''')

    # Opt-out requests table
    cursor.execute('''
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
    conn.close()
    print(f"Database initialized at {db_path}")

if __name__ == "__main__":
    init_db()
