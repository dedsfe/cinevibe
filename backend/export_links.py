import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "links.db")

def export_links():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("SELECT * FROM links ORDER BY added_at DESC")
        rows = c.fetchall()
        
        output_file = "scraped_urls.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"{'TITLE':<40} | {'STATUS / URL'}\n")
            f.write("-" * 100 + "\n")
            for row in rows:
                title = row["title"]
                url = row["embed_url"]
                # tmdb = row["tmdb_id"]
                # date = row["added_at"]
                f.write(f"{title:<40} | {url}\n")
        
        print(f"Exported {len(rows)} links to {output_file}")
        
        # Print to console as well for immediate visibility
        print("-" * 100)
        with open(output_file, "r") as f:
            print(f.read())
            
    except Exception as e:
        print(f"Error exporting: {e}")
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    export_links()
