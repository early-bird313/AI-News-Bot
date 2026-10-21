import asyncio
import logging
import aiohttp
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import List, Dict, Any, Optional
from .sources import SOURCES

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "AINewsDigestBot/1.0 (Windows NT 10.0; Win64; x64; Local News Aggregator; +https://github.com)",
    "Accept": "application/rss+xml, application/xml, application/json, text/xml, */*"
}

def clean_html_text(html_content: str) -> str:
    """Strips HTML tags and normalizes whitespace."""
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "html.parser")
    # Remove script and style tags
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    return " ".join(text.split()).strip()

def parse_feed_date(entry: Any) -> str:
    """Extracts a reliable ISO timestamp from feed entry."""
    for field in ["published_parsed", "updated_parsed", "created_parsed"]:
        val = getattr(entry, field, None)
        if val:
            try:
                dt = datetime(*val[:6])
                return dt.isoformat()
            except Exception:
                pass
                
    for field in ["published", "updated", "pubDate"]:
        val = getattr(entry, field, None)
        if val and isinstance(val, str):
            try:
                dt = parsedate_to_datetime(val)
                return dt.isoformat()
            except Exception:
                pass
                
    return datetime.now().isoformat()

FALLBACK_IMAGES = {
    "LLM": "https://images.unsplash.com/photo-1677442136019-21780ecad995?auto=format&fit=crop&w=600&q=80",
    "Research": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=600&q=80",
    "Hardware": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=600&q=80",
    "Open Source": "https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&w=600&q=80",
    "Industry": "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=600&q=80",
    "Tech News": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=600&q=80",
    "Community": "https://images.unsplash.com/photo-1531482615713-2afd69097998?auto=format&fit=crop&w=600&q=80",
    "General AI": "https://images.unsplash.com/photo-1677442136019-21780ecad995?auto=format&fit=crop&w=600&q=80"
}

def extract_image_from_entry(entry: Any, raw_html: str, category: str) -> str:
    """Extracts image URL from RSS media tags or HTML, or provides high-res fallback."""
    # 1. Media content
    if hasattr(entry, "media_content") and entry.media_content:
        for m in entry.media_content:
            if isinstance(m, dict) and m.get("url"):
                return m["url"]
                
    # 2. Media thumbnail
    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        for m in entry.media_thumbnail:
            if isinstance(m, dict) and m.get("url"):
                return m["url"]

    # 3. Enclosures
    if hasattr(entry, "enclosures") and entry.enclosures:
        for enc in entry.enclosures:
            if isinstance(enc, dict) and enc.get("type", "").startswith("image/") and enc.get("href"):
                return enc["href"]

    # 4. Search in HTML body
    if raw_html:
        try:
            soup = BeautifulSoup(raw_html, "html.parser")
            img = soup.find("img")
            if img and img.get("src"):
                src = img["src"]
                if src.startswith("http") and not any(skip in src for skip in ["tracker", "pixel", "icon"]):
                    return src
        except Exception:
            pass

    # 5. Thematic fallback
    return FALLBACK_IMAGES.get(category, FALLBACK_IMAGES["General AI"])

async def fetch_rss_feed(
    session: aiohttp.ClientSession,
    source: Dict[str, str],
    limit_per_feed: int = 15
) -> List[Dict[str, Any]]:
    """Fetches and parses a single RSS/Atom feed."""
    url = source["url"]
    source_name = source["name"]
    default_cat = source.get("default_category", "General AI")
    results = []
    
    try:
        async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                logger.warning(f"Failed to fetch {source_name} (HTTP {resp.status})")
                return []
            raw_bytes = await resp.read()
            feed = feedparser.parse(raw_bytes)
            
            for entry in feed.entries[:limit_per_feed]:
                title = getattr(entry, "title", "").strip()
                link = getattr(entry, "link", "").strip()
                
                if not title or not link:
                    continue
                    
                # Extract summary text and raw HTML for images
                raw_summary = ""
                raw_html = ""
                if hasattr(entry, "summary"):
                    raw_html = entry.summary
                    raw_summary = clean_html_text(entry.summary)
                elif hasattr(entry, "description"):
                    raw_html = entry.description
                    raw_summary = clean_html_text(entry.description)
                elif hasattr(entry, "content"):
                    raw_html = entry.content[0].value
                    raw_summary = clean_html_text(entry.content[0].value)
                    
                published_at = parse_feed_date(entry)
                image_url = extract_image_from_entry(entry, raw_html, default_cat)
                
                results.append({
                    "title": title,
                    "url": link,
                    "image_url": image_url,
                    "source": source_name,
                    "default_category": default_cat,
                    "published_at": published_at,
                    "raw_summary": raw_summary[:1200]
                })
    except asyncio.TimeoutError:
        logger.warning(f"Timeout fetching {source_name}")
    except Exception as e:
        logger.error(f"Error scraping {source_name}: {e}")
        
    return results

async def fetch_hackernews_ai(
    session: aiohttp.ClientSession,
    source: Dict[str, str],
    limit: int = 30
) -> List[Dict[str, Any]]:
    """Fetches top Hacker News items and filters for AI-relevant headlines."""
    results = []
    ai_keywords = [
        " ai ", "ai:", "ai,", "llm", "gpt", "claude", "gemini", "llama", "deepseek",
        "openai", "anthropic", "machine learning", "deep learning", "neural",
        "diffusion", "rag", "transformer", "embedding", "agent", "weights"
    ]
    
    try:
        top_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        async with session.get(top_url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status != 200:
                return []
            story_ids = await resp.json()
            story_ids = story_ids[:limit]
            
        async def fetch_story(sid: int):
            try:
                item_url = f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
                async with session.get(item_url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=5)) as item_resp:
                    if item_resp.status == 200:
                        return await item_resp.json()
            except Exception:
                return None
            return None

        stories = await asyncio.gather(*[fetch_story(sid) for sid in story_ids])
        
        for story in stories:
            if not story or story.get("type") != "story":
                continue
            title = story.get("title", "")
            title_padded = f" {title.lower()} "
            
            # Check if relevant to AI
            if any(kw in title_padded for kw in ai_keywords):
                url = story.get("url") or f"https://news.ycombinator.com/item?id={story.get('id')}"
                time_val = story.get("time")
                published_at = datetime.fromtimestamp(time_val).isoformat() if time_val else datetime.now().isoformat()
                score = story.get("score", 0)
                
                results.append({
                    "title": title,
                    "url": url,
                    "image_url": FALLBACK_IMAGES["Community"],
                    "source": "Hacker News AI",
                    "default_category": "Community",
                    "published_at": published_at,
                    "raw_summary": f"Discussion on Hacker News with {score} points and {story.get('descendants', 0)} comments."
                })
    except Exception as e:
        logger.error(f"Error fetching Hacker News AI: {e}")
        
    return results

async def fetch_all_sources() -> List[Dict[str, Any]]:
    """Crawls all configured AI news feeds concurrently."""
    all_raw_articles: List[Dict[str, Any]] = []
    
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        for src in SOURCES:
            if src.get("type") == "rss":
                tasks.append(fetch_rss_feed(session, src))
            elif src.get("type") == "hackernews":
                tasks.append(fetch_hackernews_ai(session, src))
                
        feed_results = await asyncio.gather(*tasks, return_exceptions=True)
        for res in feed_results:
            if isinstance(res, list):
                all_raw_articles.extend(res)
                
    return all_raw_articles
