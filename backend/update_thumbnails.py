import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "news.db"

CATEGORY_IMAGES = {
    "LLM": "https://images.unsplash.com/photo-1677442136019-21780ecad995?auto=format&fit=crop&w=600&q=80",
    "Research": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=600&q=80",
    "Hardware": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=600&q=80",
    "Open Source": "https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&w=600&q=80",
    "Industry": "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=600&q=80",
    "Tech News": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=600&q=80",
    "Community": "https://images.unsplash.com/photo-1531482615713-2afd69097998?auto=format&fit=crop&w=600&q=80",
    "General AI": "https://images.unsplash.com/photo-1677442136019-21780ecad995?auto=format&fit=crop&w=600&q=80"
}

TOPIC_IMAGES = [
    (["apple", "siri", "iphone"], "https://images.unsplash.com/photo-1510557880182-3d4d3cba35a5?auto=format&fit=crop&w=600&q=80"),
    (["weather", "cyclone", "climate"], "https://images.unsplash.com/photo-1504608524841-42fe6f032b4b?auto=format&fit=crop&w=600&q=80"),
    (["chip", "gpu", "nvidia", "hardware", "semiconductor"], "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=600&q=80"),
    (["robot", "agent", "autonomous"], "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?auto=format&fit=crop&w=600&q=80"),
    (["code", "github", "developer", "pytorch"], "https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&w=600&q=80"),
    (["biotech", "biology", "science", "alphafold"], "https://images.unsplash.com/photo-1532094349884-543bc11b234d?auto=format&fit=crop&w=600&q=80"),
    (["openai", "gpt", "altman"], "https://images.unsplash.com/photo-1677442136019-21780ecad995?auto=format&fit=crop&w=600&q=80")
]

def update_thumbnails():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # 1. Ensure image_url column exists
    try:
        cursor.execute("ALTER TABLE news_items ADD COLUMN image_url TEXT;")
        conn.commit()
    except sqlite3.OperationalError:
        pass
        
    # 2. Update existing rows
    cursor.execute("SELECT id, title, category, image_url FROM news_items")
    rows = cursor.fetchall()
    
    updated = 0
    for row in rows:
        row_id, title, category, existing_img = row
        if existing_img and existing_img.strip():
            continue
            
        # Match topic keywords
        title_l = title.lower()
        matched_img = None
        for keywords, img_url in TOPIC_IMAGES:
            if any(k in title_l for k in keywords):
                matched_img = img_url
                break
                
        if not matched_img:
            matched_img = CATEGORY_IMAGES.get(category, CATEGORY_IMAGES["General AI"])
            
        cursor.execute("UPDATE news_items SET image_url = ? WHERE id = ?", (matched_img, row_id))
        updated += 1
        
    conn.commit()
    conn.close()
    print(f"[SUCCESS] Updated {updated} items with thumbnail images.")

if __name__ == "__main__":
    update_thumbnails()
