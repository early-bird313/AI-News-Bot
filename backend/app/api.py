from fastapi import APIRouter, Query, BackgroundTasks, HTTPException
from typing import Optional, List, Dict, Any
from datetime import datetime

from .config import settings
from .models import NewsItem, SystemStatus
from .database import get_news, get_stats, get_pending_digest_items
from .scheduler import scheduler_engine
from .telegram_bot import dispatch_digest_to_telegram
from .email_sender import dispatch_digest_to_email

router = APIRouter(prefix="/api")

@router.get("/news", response_model=List[NewsItem])
async def list_news(
    filter: str = Query("all", description="Filter type: all, trending, latest"),
    category: Optional[str] = Query(None, description="Category filter"),
    search: Optional[str] = Query(None, description="Search query"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    items = get_news(
        limit=limit,
        offset=offset,
        filter_type=filter,
        category=category or "",
        search=search or ""
    )
    return items

@router.get("/status", response_model=SystemStatus)
async def get_system_status():
    settings.reload_from_env()
    stats = get_stats()
    email_user = settings.EMAIL_USERNAME or settings.EMAIL_RECIPIENT
    return SystemStatus(
        is_running=True,
        last_fetch_time=scheduler_engine.last_fetch_time.isoformat() if scheduler_engine.last_fetch_time else None,
        next_fetch_time=scheduler_engine.get_next_fetch_time(),
        next_digest_time=scheduler_engine.get_next_digest_time(),
        total_news_count=stats["total_news"],
        trending_news_count=stats["trending_news"],
        telegram_configured=bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID),
        gemini_configured=bool(settings.GEMINI_API_KEY),
        email_configured=bool(email_user and settings.EMAIL_PASSWORD)
    )

@router.post("/fetch-now")
async def trigger_fetch_now(background_tasks: BackgroundTasks):
    """Triggers an immediate background crawl of all feeds."""
    background_tasks.add_task(scheduler_engine.run_news_crawler)
    return {"message": "Background fetch triggered successfully"}

@router.post("/send-digest")
async def trigger_test_digest():
    """Manually triggers a digest send to Telegram right now."""
    settings.reload_from_env()
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        raise HTTPException(
            status_code=400,
            detail="Telegram credentials (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID) are not configured in .env file."
        )
        
    result = await scheduler_engine.run_scheduled_digest(period="manual")
    return result

@router.post("/send-email-digest")
async def trigger_email_digest():
    """Manually triggers an HTML newsletter send to Email right now."""
    settings.reload_from_env()
    email_user = (settings.EMAIL_USERNAME or settings.EMAIL_RECIPIENT).strip()
    email_pass = settings.EMAIL_PASSWORD.replace(" ", "").strip()
    
    if not email_user or not email_pass:
        raise HTTPException(
            status_code=400,
            detail="ইমেইল পাঠানো যায়নি: .env ফাইলে EMAIL_USERNAME (Gmail) অথবা EMAIL_PASSWORD (App Password) পাওয়া যায়নি।"
        )
    
    items = get_pending_digest_items(limit=5, min_score=5.5)
    result = await dispatch_digest_to_email(items, period="manual")
    if result.get("status") != "success":
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to send email"))
    return result

@router.get("/categories")
async def get_categories() -> List[str]:
    return ["All", "LLM", "Research", "Open Source", "Hardware", "Industry", "Tech News", "Community"]
