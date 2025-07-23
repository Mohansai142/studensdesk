import sqlite3

conn = sqlite3.connect("database/education.db")
cursor = conn.cursor()

# Add 'role' column if not exists
try:
    cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'student';")
    print("✅ 'role' column added.")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("⚠️ 'role' column already exists.")
    else:
        raise

conn.commit()
conn.close()
