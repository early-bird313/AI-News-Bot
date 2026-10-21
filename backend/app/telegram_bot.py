import re
import html
import asyncio
import logging
import aiohttp
from typing import List, Optional
from datetime import datetime
from .config import settings
from .models import NewsItem

logger = logging.getLogger(__name__)

BN_MONTHS = {
    1: "জানুয়ারি", 2: "ফেব্রুয়ারি", 3: "মার্চ", 4: "এপ্রিল",
    5: "মে", 6: "জুন", 7: "জুলাই", 8: "আগস্ট",
    9: "সেপ্টেম্বর", 10: "অক্টোবর", 11: "নভেম্বর", 12: "ডিসেম্বর"
}
BN_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")

def to_bn_num(n) -> str:
    """Converts english digits to Bengali digits."""
    return str(n).translate(BN_DIGITS)

def get_bengali_date(dt: datetime) -> str:
    """Returns Bengali formatted date like '১৪ সেপ্টেম্বর ২০২৬'."""
    d = to_bn_num(dt.day)
    m = BN_MONTHS.get(dt.month, "সেপ্টেম্বর")
    y = to_bn_num(dt.year)
    return f"{d} {m} {y}"

def esc(text: str) -> str:
    """Escapes HTML characters specifically for Telegram HTML mode."""
    if not text:
        return ""
    text = text.replace("&#x27;", "'").replace("&quot;", '"').replace("&amp;", "&")
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def clean_summary_text(item: NewsItem) -> str:
    """Extracts a neat, professional 1-2 line summary."""
    if item.ai_summary_bn:
        lines = [l.strip() for l in item.ai_summary_bn.split("\n") if l.strip()]
        cleaned = []
        for l in lines:
            clean = re.sub(r"^[•📌⚡💡\s]+", "", l).strip()
            for prefix in ["ঘটনা:", "কী ঘটেছে:", "গুরুত্ব:", "ফলাফল:", "তথ্য:"]:
                if clean.startswith(prefix):
                    clean = clean[len(prefix):].strip()
            # If line is just the english title followed by generic bangla suffix, clean it
            clean = re.sub(r"^.*?এআই প্রযুক্তি ও সংশ্লিষ্ট ফিল্ডে এটি একটি গুরুত্বপূর্ণ আপডেট।?", "এআই প্রযুক্তি বিশ্বে এটি একটি বিশেষ গুরুত্বপূর্ণ আপডেট।", clean).strip()
            if clean and not (clean.startswith("http") or clean.startswith("Original:")):
                cleaned.append(clean)
            if len(cleaned) >= 2:
                break
        if cleaned:
            return " ".join(cleaned)
            
    if item.raw_summary:
        raw = re.sub(r"<[^>]+>", "", item.raw_summary).strip()
        if raw:
            return raw[:160] + "..."
            
    return "এআই প্রযুক্তির এই নতুন অগ্রগতি সম্পর্কে বিস্তারিত জানতে নিচের লিংকে ক্লিক করুন।"

def get_trending_topic(items: List[NewsItem]) -> str:
    """Derives a dynamic trending topic from the top news."""
    text_corpus = " ".join([f"{it.title} {it.title_bn} {it.category}" for it in items]).lower()
    if "agent" in text_corpus or "reasoning" in text_corpus or "benchmark" in text_corpus:
        return "AI Reasoning & Agent Evaluation"
    elif "distill" in text_corpus or "weights" in text_corpus or "open-source" in text_corpus:
        return "Frontier LLM & Model Distillation"
    elif "chip" in text_corpus or "gpu" in text_corpus or "hardware" in text_corpus:
        return "Next-Gen AI Hardware & Compute"
    elif "cyclone" in text_corpus or "science" in text_corpus or "biology" in text_corpus:
        return "AI in Scientific Discovery & Forecasting"
    return "Breakthrough Foundation Models & Tools"

def format_telegram_digest(items: List[NewsItem], period: str = "manual") -> List[str]:
    """
    Formats news items into the exact 'AI Intelligence Brief' template requested by the user.
    """
    top_items = items[:5]
    if not top_items:
        return ["🤖 <b>AI Intelligence Brief</b>\n\nবর্তমানে নতুন কোনো উল্লেখযোগ্য এআই সংবাদ নেই। পরবর্তী শিডিউলে আবার আপডেট জানানো হবে।"]

    now = datetime.now()
    date_bn = get_bengali_date(now)

    # Time & Next update strings
    if period == "morning":
        time_text = "সকাল ১০:০০টা"
        next_update = "আজ দুপুর ২:০০টা"
    elif period == "afternoon":
        time_text = "দুপুর ২:০০টা"
        next_update = "আজ রাত ৯:০০টা"
    elif period == "night":
        time_text = "রাত ৯:০০টা"
        next_update = "আগামীকাল সকাল ১০:০০টা"
    else:
        hr = now.hour
        mn = now.minute
        period_name = "সকাল" if hr < 12 else ("দুপুর" if hr < 16 else ("সন্ধ্যা" if hr < 19 else "রাত"))
        hr12 = hr if hr <= 12 else hr - 12
        if hr12 == 0: hr12 = 12
        time_text = f"{period_name} {to_bn_num(hr12)}:{to_bn_num(f'{mn:02d}')}টা"
        
        # Calculate accurate next scheduled update
        if hr < 10:
            next_update = "আজ সকাল ১০:০০টা"
        elif hr < 14:
            next_update = "আজ দুপুর ২:০০টা"
        elif hr < 21:
            next_update = "আজ রাত ৯:০০টা"
        else:
            next_update = "আগামীকাল সকাল ১০:০০টা"

    # Category counts for landscape
    research_count = sum(1 for it in top_items if it.category == "Research")
    industry_count = sum(1 for it in top_items if it.category in ["Industry", "Tech News"])
    tools_count = sum(1 for it in top_items if it.category in ["LLM", "Tool", "Open Source"])
    business_count = sum(1 for it in top_items if it.category in ["Community", "Business"])

    trending_topic = get_trending_topic(top_items)

    featured = top_items[0]
    rest_items = top_items[1:]

    msg_lines = []

    # 1. Header
    msg_lines.append("🚀 <b>আজকের AI Intelligence Brief</b>\n")
    msg_lines.append(f"📅 <b>{date_bn}</b>")
    msg_lines.append(f"🕙 <b>{time_text} · Bangladesh Time</b>\n")
    msg_lines.append("━━━━━━━━━━━━━━━━━━\n")

    # 2. Main Featured Story (#1)
    feat_title = esc(featured.title_bn or featured.title)
    feat_cat = esc(featured.category)
    feat_score = f"{featured.impact_score:.1f}" if featured.impact_score else "8.5"
    feat_summary = esc(clean_summary_text(featured))
    feat_source = esc(featured.source)

    msg_lines.append(f"<b>🧠 {feat_title}</b>\n")
    msg_lines.append(f"🏷️ <b>{feat_cat}</b> · 🔥 <b>Impact {feat_score}/10</b>\n")
    msg_lines.append(f"{feat_summary}\n")
    msg_lines.append(f"📚 <b>Source:</b> {feat_source}")
    msg_lines.append("📅 <b>Published:</b> Today\n")
    msg_lines.append(f"👉 <a href=\"{featured.url}\"><b>মূল খবরটি পড়ুন ↗</b></a>\n")
    msg_lines.append("━━━━━━━━━━━━━━━━━━\n")

    # 3. Secondary Stories (#2 to #5)
    if rest_items:
        msg_lines.append("<b>🔬 আরও শীর্ষ AI সংবাদ</b>\n")

        for idx, item in enumerate(rest_items, 2):
            num_str = f"{idx:02d}"
            item_title = esc(item.title_bn or item.title)
            item_summary = esc(clean_summary_text(item))
            item_cat = esc(item.category)
            item_score = f"{item.impact_score:.1f}" if item.impact_score else "7.5"
            item_source = esc(item.source)

            msg_lines.append(f"<b>{num_str} | {item_title}</b>\n")
            msg_lines.append(f"{item_summary}\n")
            msg_lines.append(f"🏷️ <b>{item_cat}</b> · 🔥 <b>Impact {item_score}/10</b>")
            msg_lines.append(f"📚 {item_source}\n")
            msg_lines.append(f"👉 <a href=\"{item.url}\"><b>মূল খবরটি পড়ুন ↗</b></a>\n")

            if idx < len(rest_items) + 1:
                msg_lines.append("──────────────────\n")

        msg_lines.append("━━━━━━━━━━━━━━━━━━\n")

    # 4. Landscape Summary
    msg_lines.append("📊 <b>আজকের AI Landscape</b>\n")
    msg_lines.append(f"🔬 Research ━━━━━ {research_count}")
    msg_lines.append(f"🏢 Industry ━━━━━ {industry_count}")
    msg_lines.append(f"🛠️ Tools & Models ━ {tools_count}")
    msg_lines.append(f"💼 AI Business ━━━ {business_count}\n")
    msg_lines.append("🔥 <b>Trending Topic:</b>")
    msg_lines.append(f"<b>{trending_topic}</b>\n")
    msg_lines.append("━━━━━━━━━━━━━━━━━━\n")

    # 5. Footer
    msg_lines.append("🤖 <b>AI Intelligence Brief</b>")
    msg_lines.append("<i>সংগৃহীত • বিশ্লেষিত • Ranked by AI</i>\n")
    msg_lines.append(f"📌 পরবর্তী আপডেট: <b>{next_update}</b>")

    full_message = "\n".join(msg_lines)
    return [full_message]

def get_telegram_chat_ids() -> List[str]:
    """Returns a list of target chat IDs (personal, groups, channels)."""
    raw = settings.TELEGRAM_CHAT_ID or ""
    parts = re.split(r'[,;\s]+', raw.strip())
    return [p.strip() for p in parts if p.strip()]

async def send_telegram_message(html_text: str, chat_id: str) -> bool:
    """Sends a single message to Telegram using Bot API with HTML parse mode."""
    bot_token = settings.TELEGRAM_BOT_TOKEN

    if not bot_token or not chat_id:
        logger.warning("Telegram Bot Token or Chat ID is not configured in .env.")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": html_text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    return True
                else:
                    err = await resp.text()
                    logger.error(f"Telegram API error for chat {chat_id} ({resp.status}): {err}")
                    return False
    except Exception as e:
        logger.error(f"Failed to send Telegram message to {chat_id}: {e}")
        return False

async def dispatch_digest_to_telegram(items: List[NewsItem], period: str = "manual") -> bool:
    """Dispatches clean AI Intelligence Brief digest to all configured Telegram chats/groups."""
    settings.reload_from_env()
    chat_ids = get_telegram_chat_ids()

    if not chat_ids or not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("Telegram Bot Token or Chat ID is not configured in .env.")
        return False

    chunks = format_telegram_digest(items, period)
    any_success = False

    for cid in chat_ids:
        chat_ok = True
        for chunk in chunks:
            ok = await send_telegram_message(chunk, cid)
            if not ok:
                chat_ok = False
        if chat_ok:
            any_success = True
            logger.info(f"Telegram digest successfully sent to chat {cid}.")

    return any_success

async def send_welcome_message(chat_id: int | str):
    """Sends a friendly Bengali welcome message when the bot joins a group."""
    welcome_text = (
        "👋 <b>হ্যালো সবাইকে! আমি AI News Bot</b> 🤖\n\n"
        "আমাকে <b>মিনহাজ ভাই</b> এই গ্রুপে যুক্ত করেছেন।\n\n"
        "আমি প্রতিদিন বিশ্বের সেরা ও ট্রেন্ডিং <b>Top 5 AI নিউজ আপডেট</b> সরাসরি সোর্স লিংকসহ আপনাদের জানাবো:\n"
        "🕙 <b>সকাল ১০:০০টা</b>\n"
        "🕑 <b>দুপুর ২:০০টা</b>\n"
        "🕙 <b>রাত ১০:০০টা</b>\n\n"
        "সর্বশেষ কৃত্রিম বুদ্ধিমত্তা ও প্রযুক্তি বিশ্বের গুরুত্বপূর্ণ খবর পেতে চোখ রাখুন! 🚀"
    )
    await send_telegram_message(welcome_text, str(chat_id))

def auto_save_chat_id_to_env(new_chat_id: str):
    """Automatically records newly discovered group chat ID into .env."""
    try:
        from pathlib import Path
        env_file = Path(__file__).resolve().parent.parent.parent / ".env"
        if not env_file.exists():
            return
        lines = env_file.read_text(encoding="utf-8").splitlines()
        new_lines = []
        for line in lines:
            if line.startswith("TELEGRAM_CHAT_ID="):
                val = line.split("=", 1)[1].strip()
                if new_chat_id not in val:
                    val = f"{val}, {new_chat_id}" if val else new_chat_id
                    new_lines.append(f"TELEGRAM_CHAT_ID={val}")
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        env_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        settings.reload_from_env()
        logger.info(f"Auto-saved new chat ID {new_chat_id} to .env")
    except Exception as e:
        logger.error(f"Failed to auto-save chat ID: {e}")

async def poll_telegram_updates_loop():
    """Background listener that detects group additions and interactive commands."""
    offset = None
    logger.info("Telegram background listener started.")

    while True:
        try:
            settings.reload_from_env()
            token = settings.TELEGRAM_BOT_TOKEN
            if not token:
                await asyncio.sleep(10)
                continue

            url = f"https://api.telegram.org/bot{token}/getUpdates"
            params = {"timeout": 25}
            if offset is not None:
                params["offset"] = offset

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=35)) as resp:
                    if resp.status != 200:
                        await asyncio.sleep(5)
                        continue
                    data = await resp.json()

            results = data.get("result", [])
            for update in results:
                update_id = update["update_id"]
                offset = update_id + 1

                # 1. Event: Bot added to a group (my_chat_member)
                if "my_chat_member" in update:
                    mcm = update["my_chat_member"]
                    new_status = mcm.get("new_chat_member", {}).get("status")
                    if new_status in ("member", "administrator"):
                        chat = mcm.get("chat", {})
                        cid = chat.get("id")
                        if cid:
                            logger.info(f"Bot joined group: {chat.get('title')} ({cid})")
                            auto_save_chat_id_to_env(str(cid))
                            await send_welcome_message(cid)

                # 2. Event: Message in group or private chat
                if "message" in update:
                    msg = update["message"]
                    chat = msg.get("chat", {})
                    cid = chat.get("id")
                    text = (msg.get("text") or "").strip().lower()

                    # Check if bot was in new_chat_members
                    new_members = msg.get("new_chat_members", [])
                    bot_added = any(m.get("is_bot") and m.get("username", "").endswith("bot") for m in new_members)
                    if bot_added and cid:
                        auto_save_chat_id_to_env(str(cid))
                        await send_welcome_message(cid)

                    # Interactive Commands: /test or /news
                    if text.startswith("/test") or text.startswith("/news"):
                        from .database import get_pending_digest_items
                        items = get_pending_digest_items(limit=5, min_score=5.0)
                        chunks = format_telegram_digest(items, period="manual")
                        for chunk in chunks:
                            await send_telegram_message(chunk, str(cid))

                    elif text.startswith("/start") or text.startswith("/help"):
                        help_text = (
                            "🤖 <b>AI Intelligence Brief Bot</b>\n\n"
                            "আমি প্রতিদিন সকাল ১০:০০, দুপুর ২:০০ ও রাত ১০:০০টায় বিশ্বের সেরা Top 5 AI নিউজ পাঠাই।\n\n"
                            "কমান্ডসমূহ:\n"
                            "• <code>/news</code> বা <code>/test</code> - এখনই সর্বশেষ এআই ডাইজেস্ট দেখুন\n"
                            "• <code>/help</code> - এই সাহায্য মেসেজটি দেখুন"
                        )
                        await send_telegram_message(help_text, str(cid))

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.debug(f"Telegram polling loop exception: {e}")
            await asyncio.sleep(5)


