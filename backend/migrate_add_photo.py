"""
Run this ONCE to add photo_path column to existing database.
Usage:  cd backend && python migrate_add_photo.py
"""
import os, sys, sqlite3
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'aarogyalink.db')
DB_PATH = os.path.abspath(DB_PATH)

print(f"Database: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)
cur  = conn.cursor()

# Check existing columns
cur.execute("PRAGMA table_info(patients)")
cols = [row[1] for row in cur.fetchall()]
print(f"Existing columns: {cols}")

if 'photo_path' not in cols:
    cur.execute("ALTER TABLE patients ADD COLUMN photo_path VARCHAR(255)")
    conn.commit()
    print("✅ photo_path column added successfully!")
else:
    print("✅ photo_path column already exists — database is up to date!")

conn.close()