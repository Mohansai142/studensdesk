import sqlite3

conn = sqlite3.connect("database/education.db")
cursor = conn.cursor()

# Insert teacher
username = "teacher1"
password = "pass123"
role = "teacher"

cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
               (username, password, role))

conn.commit()
conn.close()

print("✅ Teacher added.")
