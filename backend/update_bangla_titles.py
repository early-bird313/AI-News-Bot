import sqlite3
import json
from pathlib import Path
from app.config import settings
from google import genai
from google.genai import types

DB_PATH = Path(__file__).resolve().parent / "news.db"

def update_titles_with_gemini(limit: int = 30):
    if not settings.GEMINI_API_KEY:
        print("[INFO] No Gemini API key found.")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Select top trending and recent items
    cursor.execute("""
        SELECT id, title, raw_summary 
        FROM news_items 
        ORDER BY impact_score DESC, id DESC 
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    
    print(f"[INFO] Translating/generating catchy Bengali headlines for top {len(rows)} news items using Gemini...")
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    # Process in batches of 5
    batch_size = 5
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        items_payload = [{"id": r[0], "title": r[1]} for r in batch]
        
        prompt = f"""
Translate and write natural, compelling, and accurate news headlines in Bengali (বাংলা শিরোনাম) for these AI news titles:
{json.dumps(items_payload, ensure_ascii=False)}

Return JSON list:
[
  {{"id": 1, "title_bn": "বাংলায় চমৎকার ও প্রফেশনাল সংবাদ শিরোনাম"}}
]
"""
        try:
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2
                )
            )
            if response.text:
                results = json.loads(response.text.strip())
                for item in results:
                    cursor.execute(
                        "UPDATE news_items SET title_bn = ? WHERE id = ?",
                        (item.get("title_bn"), item.get("id"))
                    )
                conn.commit()
                print(f"[SUCCESS] Processed batch {i//batch_size + 1} ({len(results)} titles).")
        except Exception as e:
            print(f"[ERROR] Gemini batch error: {e}")
            break
            
    conn.close()
    print("[DONE] Finished updating Bengali headlines.")

if __name__ == "__main__":
    update_titles_with_gemini(limit=30)
