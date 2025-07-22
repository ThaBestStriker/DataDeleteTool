import os
import sqlite3  # For unencrypted mode
import sqlcipher3  # For encrypted mode

def init_db(passphrase):
    """Initialize SQLite database for GHOSTWIPE (encrypted or unencrypted)."""
    db_path = os.path.join('data', 'pii_data.db')
    if passphrase:
        sqlite = sqlcipher3
    else:
        sqlite = sqlite3
    conn = sqlite.connect(db_path)
    try:
        if passphrase:
            conn.execute(f"PRAGMA key = '{passphrase}'")  # Set AES-256 encryption key
            conn.execute("PRAGMA kdf_iter = 640000")  # High iterations for brute-force resistance
            conn.execute("PRAGMA cipher_page_size = 4096")  # Optimize for security/performance
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
        # Usernames table (for social media accounts)
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
        # Verify by running a simple query
        conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise
    finally:
        conn.close()