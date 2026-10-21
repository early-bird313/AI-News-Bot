from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

class NewsItem(BaseModel):
    id: Optional[int] = None
    title: str
    title_bn: str = ""
    normalized_title: str = ""
    url: str
    image_url: Optional[str] = None
    source: str
    category: str = "General AI"
    published_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    raw_summary: str = ""
    ai_summary_bn: str = ""
    impact_score: float = 5.0
    is_trending: bool = False
    title_hash: str = ""
    sent_in_digest: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class DigestLog(BaseModel):
    id: Optional[int] = None
    sent_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    period: str = "scheduled" # morning_10am, afternoon_2pm, night_9pm, manual
    item_count: int = 0
    status: str = "success"
    error_message: Optional[str] = None

class SystemStatus(BaseModel):
    is_running: bool = True
    last_fetch_time: Optional[str] = None
    next_fetch_time: Optional[str] = None
    next_digest_time: Optional[str] = None
    total_news_count: int = 0
    trending_news_count: int = 0
    telegram_configured: bool = False
    gemini_configured: bool = False
    email_configured: bool = False
