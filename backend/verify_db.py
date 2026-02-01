import sqlite3
import os

DB_PATH = "links.db"

if not os.path.exists(DB_PATH):
    print("Database not found!")
    exit(1)

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Check for 'rei'
c.execute("SELECT * FROM links WHERE title LIKE ?", ('%rei%',))
rows = c.fetchall()

if rows:
    print("Found entries:")
    for row in rows:
        print(row)
else:
    print("No entries found for 'rei'")

conn.close()
