import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "links.db")

def migrate():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        c.execute("ALTER TABLE links ADD COLUMN poster_path TEXT")
        print("Added poster_path column.")
    except Exception as e:
        print(f"poster_path error (maybe exists): {e}")

    try:
        c.execute("ALTER TABLE links ADD COLUMN backdrop_path TEXT")
        print("Added backdrop_path column.")
    except Exception as e:
        print(f"backdrop_path error (maybe exists): {e}")
        
    try:
        c.execute("ALTER TABLE links ADD COLUMN overview TEXT")
        print("Added overview column.")
    except Exception as e:
        print(f"overview error (maybe exists): {e}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
