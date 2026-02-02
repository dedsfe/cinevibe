from playwright_scraper import scrape_operatopzera
from database import save_embed
import logging

logging.basicConfig(level=logging.INFO)

def force_add():
    print("Forcing scrape for Interestelar...")
    # Use Portuguese title as found on site
    video_url = scrape_operatopzera("Interestelar", year="2014")
    
    if video_url:
        print(f"FOUND: {video_url}")
        # Save with TMDB data
        save_embed(
            title="Interestelar", 
            embed_url=video_url, 
            tmdb_id="157336",
            poster_path="/gEU2QniL6E77NI6lCU6MxlNBvIx.jpg", 
            backdrop_path="/rAiYTfKGqDCRIIqo664sY9XZIvQ.jpg",
            overview="As reservas naturais da Terra estão chegando ao fim e um grupo de astronautas recebe a missão de verificar possíveis planetas para receberem a população mundial."
        )
        print("Saved to DB!")
    else:
        print("Failed to scrape.")

if __name__ == "__main__":
    force_add()
