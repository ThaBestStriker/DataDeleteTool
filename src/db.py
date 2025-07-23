import os
import sqlite3  # For unencrypted mode
import sqlcipher3  # For encrypted mode
import requests
import pdfplumber
import re
import datetime
import unicodedata
import io

def init_db(passphrase):
    """Initialize SQLite database for GHOSTWIPE (encrypted or unencrypted)."""
    db_path = os.path.join('data', 'pii_data.db')
    if passphrase:
        sqlite = sqlcipher3
    else:
        sqlite = sqlite3
    conn = sqlite.connect(db_path)
    debug_output = []
    try:
        if passphrase:
            conn.execute(f"PRAGMA key = '{passphrase}'")  # Use raw passphrase
            conn.execute("PRAGMA kdf_iter = 64000")  # Reduced iterations for compatibility
            conn.execute("PRAGMA cipher_page_size = 4096")
            debug_output.append("SQLCipher PRAGMA settings applied: key, kdf_iter=64000, cipher_page_size=4096")
        conn.execute("PRAGMA foreign_keys = ON")
        debug_output.append("Foreign keys enabled")
        
        # Create tables if they don't exist (no dropping to preserve data)
        conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            middle_name TEXT,
            last_name TEXT,
            primary_email TEXT,
            primary_phone TEXT,
            state TEXT
        )
        ''')
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
        conn.execute('''
        CREATE TABLE IF NOT EXISTS phone_numbers (
            phone_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            phone_number TEXT,
            source_site TEXT,
            is_active BOOLEAN,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
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
        conn.execute('''
        CREATE TABLE IF NOT EXISTS broker_sites (
            site_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            url TEXT,
            deletion_url TEXT,
            privacy_policy TEXT,
            contact TEXT,
            requirements TEXT,
            notes TEXT,
            last_updated TEXT
        )
        ''')
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
        conn.execute('''
        CREATE TABLE IF NOT EXISTS cleaning_records (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            site_name TEXT,
            date_cleaned TEXT,
            date_confirmed_deleted TEXT,
            FOREIGN KEY (site_id) REFERENCES broker_sites (site_id)
        )
        ''')
        conn.commit()
        debug_output.append("Database tables created or verified")
        
        # Populate broker_sites and get update date
        last_updated = populate_broker_sites(conn)
        print(f"Workbook last updated: {last_updated if last_updated else 'Unknown'}")
        conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        debug_output.append("Database initialization completed")
        print("Database initialized successfully (encrypted: {})".format(bool(passphrase)))
        
        # Write debug output to file
        debug_file = os.path.join('data', 'debug_init_output.txt')
        debug_file = backup_existing_file(debug_file)
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(debug_output))
        print(f"Initialization debug output written to {debug_file}")
        
    except Exception as e:
        debug_output.append(f"Error initializing database: {e}")
        debug_file = os.path.join('data', 'debug_init_output.txt')
        debug_file = backup_existing_file(debug_file)
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(debug_output))
        print(f"Error initializing database: {e}. Debug output written to {debug_file}")
        raise
    finally:
        conn.close()

def backup_existing_file(file_path):
    """Create a backup of an existing file with a rotating number."""
    if not os.path.exists(file_path):
        return file_path
    base, ext = os.path.splitext(file_path)
    i = 1
    while True:
        backup_path = f"{base}.bak.{i}{ext}"
        if not os.path.exists(backup_path):
            print(f"Backing up existing {file_path} to {backup_path}")
            os.rename(file_path, backup_path)
            return file_path
        i += 1

def populate_broker_sites(conn):
    """Populate broker_sites table from IntelTechniques PDF. Updates existing entries."""
    cursor = conn.cursor()
    debug_output = []
    try:
        url = "https://inteltechniques.com/data/workbook.pdf"
        # Check connectivity
        print("Checking connectivity to PDF source...")
        response = requests.head(url, timeout=5)
        if response.status_code != 200:
            debug_output.append(f"Error: Unable to connect to {url} (status code: {response.status_code})")
            print(f"Error: Unable to connect to {url} (status code: {response.status_code})")
            debug_file = os.path.join('data', 'debug_parse_output.txt')
            debug_file = backup_existing_file(debug_file)
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(debug_output))
            print(f"Debug output written to {debug_file}. Table unchanged; check connectivity.")
            return None

        print("Populating broker_sites from https://inteltechniques.com/data/workbook.pdf...")
        # Load PDF
        response = requests.get(url)
        response.raise_for_status()
        
        with pdfplumber.open(io.BytesIO(response.content)) as pdf:
            raw_text = ""
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                raw_text += page_text + "\n"
        
        raw_text = unicodedata.normalize('NFKD', raw_text).strip()
        debug_output.append("Raw text (first 1000 chars):\n" + raw_text[:1000] + "...")
        print("Raw text (first 500 chars):", raw_text[:500] + "...")
        
        # Hardcode update date to October 2024
        update_str = "October 2024"
        last_updated = "2024-10-01"
        
        # Split into entries
        entries = []
        field_map = {
            "Service:": "name",
            "Website:": "url",
            "Removal Link:": "deletion_url",
            "Privacy Policy:": "privacy_policy",
            "Contact:": "contact",
            "Requirements:": "requirements",
            "Notes:": "notes"
        }
        
        # Split raw text into entry blocks
        entry_blocks = re.split(r'\n*\s*Service:\s*', raw_text)[1:]
        debug_output.append(f"Found entry blocks: {len(entry_blocks)}")
        print(f"Found entry blocks: {len(entry_blocks)}")
        
        for i, block in enumerate(entry_blocks):
            block = block.strip()
            if not block or any(keyword in block for keyword in ['Book', 'Guide', 'Data Request', 'Credit Freeze']):
                debug_output.append(f"Skipping block {i+1}: {block[:50]}...")
                print(f"Skipping block {i+1}: {block[:50]}...")
                continue
            current_entry = {}
            # Set name from the block's first content
            name_match = re.match(r'^(.*?)(?=\n*\s*(Website:|Removal Link:|Privacy Policy:|Contact:|Requirements:|Notes:|$))', block, re.DOTALL)
            if name_match:
                name = name_match.group(1).strip()
                if name == "The name of the service":
                    debug_output.append(f"Skipping block {i+1} (placeholder name): {block[:50]}...")
                    print(f"Skipping block {i+1} (placeholder name): {block[:50]}...")
                    continue
                current_entry['name'] = name
            # Split block into fields
            fields = re.split(r'\n*\s*(Website:|Removal Link:|Privacy Policy:|Contact:|Requirements:|Notes:)', block)
            field_iter = iter(fields)
            for part in field_iter:
                part = part.strip()
                if not part or part == current_entry.get('name', ''):
                    continue
                if part in field_map:
                    try:
                        value = next(field_iter).strip()
                        key = field_map[part]
                        value = unicodedata.normalize('NFKD', value)
                        if key in ["url", "deletion_url", "privacy_policy"]:
                            value = value.strip('[] ')
                        elif key == "contact":
                            if '[email' in value or '@' not in value:
                                value = "Email protected (requires manual retrieval)"
                            else:
                                value = re.sub(r'\(/cdn-cgi/.*?\)', '', value).strip('[] ,')
                                value = re.sub(r'\[|\]', '', value)
                        elif key == "notes":
                            value = re.sub(r'\n*Date:.*?Verified Removal:.*?(?=\n|$)', '', value, flags=re.DOTALL)
                            value = re.sub(r'\n*(Copyright © \d{4} by IntelTechniques|EXTREME PRIVACY \| PERSONAL DATA REMOVAL WORKBOOK \| INTELTECHNIQUES\.COM).*', '', value, flags=re.DOTALL)
                            value = value.strip()
                        current_entry[key] = value
                    except StopIteration:
                        debug_output.append(f"Warning: Incomplete field for {part} in block {i+1}: {block[:50]}...")
                        print(f"Warning: Incomplete field for {part} in block {i+1}: {block[:50]}...")
                elif current_entry and "notes" in current_entry:
                    current_entry["notes"] += " " + part
            if current_entry and "name" in current_entry and current_entry["name"]:
                current_entry['last_updated'] = last_updated
                debug_output.append(f"Parsed entry {i+1}: {current_entry}")
                print(f"Parsed entry {i+1}: {current_entry}")
                entries.append(current_entry)
            else:
                debug_output.append(f"Skipping invalid entry {i+1} (missing or empty name): {block[:50]}...")
                print(f"Skipping invalid entry {i+1} (missing or empty name): {block[:50]}...")
        
        # Get existing entries
        cursor.execute("SELECT site_id, name, url, deletion_url, privacy_policy, contact, requirements, notes, last_updated FROM broker_sites")
        existing_entries = {row[1]: row for row in cursor.fetchall()}
        debug_output.append(f"Found {len(existing_entries)} existing broker_sites entries")
        print(f"Found {len(existing_entries)} existing broker_sites entries")
        
        # Update or insert entries
        updated_count = 0
        inserted_count = 0
        for i, entry in enumerate(entries):
            if "name" not in entry or not entry["name"]:
                debug_output.append(f"Skipping insertion {i+1} (no name): {entry}")
                print(f"Skipping insertion {i+1} (no name): {entry}")
                continue
            name = entry["name"]
            if name in existing_entries:
                # Compare fields
                existing = existing_entries[name]
                fields_to_update = []
                update_values = []
                for field in ['url', 'deletion_url', 'privacy_policy', 'contact', 'requirements', 'notes', 'last_updated']:
                    existing_value = existing[existing_entries[name][0:].index(field) + 1] or ''
                    new_value = entry.get(field, '') or ''
                    if existing_value != new_value:
                        fields_to_update.append(f"{field} = ?")
                        update_values.append(new_value)
                if fields_to_update:
                    update_values.append(existing[0])  # site_id
                    cursor.execute(f"""
                    UPDATE broker_sites
                    SET {', '.join(fields_to_update)}
                    WHERE site_id = ?
                    """, update_values)
                    updated_count += 1
                    debug_output.append(f"Updated entry {i+1}: {name}")
                    print(f"Updated entry {i+1}: {name}")
            else:
                cursor.execute('''
                INSERT OR IGNORE INTO broker_sites 
                (name, url, deletion_url, privacy_policy, contact, requirements, notes, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    entry.get("name"),
                    entry.get("url"),
                    entry.get("deletion_url"),
                    entry.get("privacy_policy"),
                    entry.get("contact"),
                    entry.get("requirements"),
                    entry.get("notes"),
                    last_updated
                ))
                inserted_count += 1
                debug_output.append(f"Inserted entry {i+1}: {name}")
                print(f"Inserted entry {i+1}: {name}")
        
        conn.commit()
        # Write debug output to file
        debug_file = os.path.join('data', 'debug_parse_output.txt')
        debug_file = backup_existing_file(debug_file)
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(debug_output))
        print(f"Debug output written to {debug_file}")
        
        print(f"Updated {updated_count} and inserted {inserted_count} broker sites successfully.")
        return update_str or last_updated
    except Exception as e:
        debug_output.append(f"Error populating broker_sites: {e}")
        debug_file = os.path.join('data', 'debug_parse_output.txt')
        debug_file = backup_existing_file(debug_file)
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(debug_output))
        print(f"Error populating broker_sites: {e}. Debug output written to {debug_file}. Table unchanged; check connectivity.")
        return None