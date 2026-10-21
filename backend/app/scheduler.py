import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from .config import settings
from .database import (
    exists_url,
    get_recent_titles,
    save_news_item,
    get_pending_digest_items,
    mark_as_sent,
    log_digest
)
from .models import NewsItem
from .scrapers import fetch_all_sources
from .deduplicator import is_duplicate_story, normalize_title, compute_title_hash
from .ai_analyzer import analyze_news_item
from .telegram_bot import dispatch_digest_to_telegram, poll_telegram_updates_loop
from .email_sender import dispatch_digest_to_email

logger = logging.getLogger(__name__)

class NewsEngineScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.last_fetch_time: Optional[datetime] = None
        self.is_fetching: bool = False
        self.listener_task: Optional[asyncio.Task] = None
        
    def start(self):
        if not self.scheduler.running:
            # 1. Digest jobs: 10:00 AM, 2:00 PM (14:00), 10:00 PM (22:00)
            self.scheduler.add_job(
                self.run_scheduled_digest,
                CronTrigger(hour=10, minute=0),
                args=["morning"],
                id="digest_morning",
                replace_existing=True
            )
            self.scheduler.add_job(
                self.run_scheduled_digest,
                CronTrigger(hour=14, minute=0),
                args=["afternoon"],
                id="digest_afternoon",
                replace_existing=True
            )
            self.scheduler.add_job(
                self.run_scheduled_digest,
                CronTrigger(hour=22, minute=0),
                args=["night"],
                id="digest_night",
                replace_existing=True
            )
            
            # 2. Continuous background crawler job (every 30 mins)
            self.scheduler.add_job(
                self.run_news_crawler,
                IntervalTrigger(minutes=settings.FETCH_INTERVAL_MINUTES),
                id="news_crawler",
                replace_existing=True
            )
            
            self.scheduler.start()
            logger.info("Scheduler started with cron triggers (10:00, 14:00, 22:00) and periodic crawler.")

            # 3. Start Telegram interactive background listener
            self.listener_task = asyncio.create_task(poll_telegram_updates_loop())
            logger.info("Telegram interactive listener background task spawned.")
            
    def shutdown(self):
        if self.listener_task:
            self.listener_task.cancel()
        if self.scheduler.running:
            self.scheduler.shutdown()

    async def run_news_crawler(self) -> Dict[str, Any]:
        """Fetches, strictly deduplicates, AI-analyzes, and saves new articles."""
        if self.is_fetching:
            return {"status": "already_running", "new_items": 0}
            
        self.is_fetching = True
        self.last_fetch_time = datetime.now()
        new_items_saved = 0
        duplicates_skipped = 0
        
        try:
            logger.info("Starting AI news monitoring crawl...")
            raw_articles = await fetch_all_sources()
            logger.info(f"Crawled {len(raw_articles)} raw entries from feeds.")
            
            # Load recent titles for strict cross-source deduplication (last 48h)
            recent_items = get_recent_titles(hours=48)
            
            for art in raw_articles:
                url = art["url"]
                title = art["title"]
                
                # Check 1: exact URL exists in DB
                if exists_url(url):
                    continue
                    
                # Check 2: strict deduplication against recent items
                is_dup, matched_item, score = is_duplicate_story(title, recent_items, similarity_threshold=78.0)
                if is_dup:
                    duplicates_skipped += 1
                    logger.debug(f"Skipping duplicate: '{title}' matched '{matched_item.get('title')}' (score: {score:.1f})")
                    continue
                    
                # Passed deduplication! Run AI analysis
                ai_result = await analyze_news_item(
                    title=title,
                    raw_summary=art.get("raw_summary", ""),
                    source_name=art["source"],
                    default_category=art.get("default_category", "General AI")
                )
                
                norm_title = normalize_title(title)
                title_h = compute_title_hash(title)
                
                news_item = NewsItem(
                    title=title,
                    title_bn=ai_result.get("title_bn", title),
                    normalized_title=norm_title,
                    url=url,
                    image_url=art.get("image_url"),
                    source=art["source"],
                    category=ai_result.get("category", "General AI"),
                    published_at=art.get("published_at", datetime.now().isoformat()),
                    raw_summary=art.get("raw_summary", ""),
                    ai_summary_bn=ai_result.get("ai_summary_bn", ""),
                    impact_score=ai_result.get("impact_score", 5.0),
                    is_trending=ai_result.get("is_trending", False),
                    title_hash=title_h,
                    sent_in_digest=False,
                    created_at=datetime.now().isoformat()
                )
                
                saved_id = save_news_item(news_item)
                if saved_id:
                    new_items_saved += 1
                    # Add newly saved item to local comparison pool
                    recent_items.append({
                        "id": saved_id,
                        "title": title,
                        "normalized_title": norm_title,
                        "title_hash": title_h,
                        "published_at": news_item.published_at,
                        "impact_score": news_item.impact_score
                    })
                    
            logger.info(f"Crawl completed. New unique stories: {new_items_saved}, Duplicates rejected: {duplicates_skipped}")
            return {
                "status": "success",
                "crawled_count": len(raw_articles),
                "new_items_saved": new_items_saved,
                "duplicates_skipped": duplicates_skipped
            }
        except Exception as e:
            logger.error(f"Error in news crawler: {e}")
            return {"status": "error", "error": str(e)}
        finally:
            self.is_fetching = False

    async def run_scheduled_digest(self, period: str = "scheduled") -> Dict[str, Any]:
        """Dispatches scheduled digest to Telegram."""
        logger.info(f"Preparing scheduled digest for period: {period}...")
        
        # 1. Fetch top pending items (highest impact score)
        items = get_pending_digest_items(limit=5, min_score=5.5)
        
        if not items:
            logger.info(f"No qualifying items for {period} digest.")
            log_digest(period=period, item_count=0, status="skipped_no_items")
            return {"status": "skipped", "reason": "no_items"}
            
        # 2. Dispatch to Telegram
        tg_success = await dispatch_digest_to_telegram(items, period=period)
        
        # 3. Dispatch to Email (if configured)
        email_result = await dispatch_digest_to_email(items, period=period)
        logger.info(f"Email digest dispatch result: {email_result}")

        if tg_success or email_result.get("status") == "success":
            item_ids = [item.id for item in items if item.id]
            mark_as_sent(item_ids)
            log_digest(period=period, item_count=len(items), status="success")
            logger.info(f"Successfully sent {len(items)} items in {period} digest.")
            return {
                "status": "success",
                "items_sent": len(items),
                "telegram": tg_success,
                "email": email_result
            }
        else:
            log_digest(period=period, item_count=len(items), status="failed", error_message="Dispatch failed")
            return {"status": "failed", "error": "Dispatch error"}

    def get_next_digest_time(self) -> Optional[str]:
        """Finds the next upcoming scheduled digest time."""
        digest_jobs = ["digest_morning", "digest_afternoon", "digest_night"]
        next_times = []
        for jid in digest_jobs:
            job = self.scheduler.get_job(jid)
            if job and job.next_run_time:
                next_times.append(job.next_run_time)
                
        if next_times:
            earliest = min(next_times)
            return earliest.isoformat()
        return None

    def get_next_fetch_time(self) -> Optional[str]:
        job = self.scheduler.get_job("news_crawler")
        if job and job.next_run_time:
            return job.next_run_time.isoformat()
        return None

scheduler_engine = NewsEngineScheduler()
