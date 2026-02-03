import sqlite3
import os

DB_PATH = os.environ.get("DB_FILE_PATH", "backend/links.db")

def migrate():
    print(f"Connecting to {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        print("Checking series table...")
        c.execute("PRAGMA table_info(series)")
        cols = [col[1] for col in c.fetchall()]
        print("Columns:", cols)
        
        if "updated_at" not in cols:
            print("Adding updated_at column...")
            c.execute("ALTER TABLE series ADD COLUMN updated_at DATETIME")
            conn.commit()
            print("✅ Column updated_at added.")
        else:
             print("✅ Column updated_at already exists.")

        # Ensure Unique Constraints (by index)
        print("Ensuring unique indexes...")
        c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_series_opera ON series(opera_id)")
        c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_seasons_uniq ON seasons(series_id, season_number)")
        c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_episodes_uniq ON episodes(series_id, season_id, episode_number)")
        print("✅ Unique indexes checked.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
