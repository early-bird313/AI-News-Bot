import html
import re
import smtplib
import asyncio
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from typing import List, Dict, Any

from .config import settings
from .models import NewsItem
from .telegram_bot import get_bengali_date, to_bn_num, get_trending_topic, clean_summary_text

logger = logging.getLogger(__name__)

def esc(text: str) -> str:
    if not text:
        return ""
    return html.escape(text)

def generate_email_html(items: List[NewsItem], period: str = "manual") -> str:
    """
    Generates a minimalist, mobile-responsive HTML newsletter email.
    """
    top_items = items[:5]
    now = datetime.now()
    date_bn = get_bengali_date(now)
    
    if period == "morning":
        time_text = "সকাল ১০:০০টা"
        period_title = "সকালের এআই ডাইজেস্ট"
    elif period == "afternoon":
        time_text = "দুপুর ২:০০টা"
        period_title = "দুপুরের এআই ডাইজেস্ট"
    elif period == "night":
        time_text = "রাত ৯:০০টা"
        period_title = "রাতের এআই ডাইজেস্ট"
    else:
        hr = now.hour
        period_name = "সকাল" if hr < 12 else ("দুপুর" if hr < 16 else ("সন্ধ্যা" if hr < 19 else "রাত"))
        time_text = f"{period_name} {to_bn_num(now.strftime('%I:%M'))}টা"
        period_title = "আজকের এআই ডাইজেস্ট"

    # Category counts
    research_count = sum(1 for it in top_items if it.category == "Research")
    industry_count = sum(1 for it in top_items if it.category in ["Industry", "Tech News"])
    tools_count = sum(1 for it in top_items if it.category in ["LLM", "Tool", "Open Source"])
    business_count = sum(1 for it in top_items if it.category in ["Community", "Business"])
    trending_topic = get_trending_topic(top_items)

    featured = top_items[0] if top_items else None
    rest_items = top_items[1:] if len(top_items) > 1 else []

    featured_img = featured.image_url if featured and featured.image_url else "https://images.unsplash.com/photo-1677442136019-21780ecad995?auto=format&fit=crop&w=800&q=80"
    
    # Secondary stories HTML
    secondary_html = ""
    for idx, item in enumerate(rest_items, 2):
        num_str = f"{idx:02d}"
        title = esc(item.title_bn or item.title)
        summary = esc(clean_summary_text(item))
        cat = esc(item.category)
        source = esc(item.source)
        score = f"{item.impact_score:.1f}" if item.impact_score else "8.0"
        
        secondary_html += f"""
        <div style="padding: 18px 0; border-bottom: 1px solid #e2e8f0;">
          <div style="font-size: 11px; font-weight: 700; color: #4f46e5; text-transform: uppercase; margin-bottom: 4px;">
            {num_str} &bull; {cat} &bull; Score {score}/10
          </div>
          <h3 style="margin: 0 0 8px 0; font-size: 16px; font-weight: 800; line-height: 1.4;">
            <a href="{item.url}" target="_blank" style="color: #0f172a; text-decoration: none;">
              {title}
            </a>
          </h3>
          <p style="margin: 0 0 10px 0; font-size: 13px; line-height: 1.5; color: #475569;">
            {summary}
          </p>
          <div style="font-size: 12px; color: #64748b;">
            <span>{source}</span> &bull; 
            <a href="{item.url}" target="_blank" style="color: #4f46e5; font-weight: 600; text-decoration: none;">
              মূল খবর পড়ুন &rarr;
            </a>
          </div>
        </div>
        """

    # Complete Newsletter HTML
    html_content = f"""<!DOCTYPE html>
<html lang="bn">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Intelligence Brief</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #0f172a;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f8fafc; padding: 25px 15px;">
    <tr>
      <td align="center">
        <!-- Main Email Container (600px Max) -->
        <table role="presentation" width="100%" style="max-width: 600px; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; overflow: hidden; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);">
          
          <!-- Header Bar -->
          <tr>
            <td style="padding: 24px 28px; background-color: #ffffff; border-bottom: 2px solid #4f46e5;">
              <table role="presentation" width="100%">
                <tr>
                  <td>
                    <div style="font-size: 11px; font-weight: 800; color: #4f46e5; letter-spacing: 0.5px; text-transform: uppercase;">
                      DAILY AI DIGEST
                    </div>
                    <h1 style="margin: 4px 0 0 0; font-size: 22px; font-weight: 900; color: #0f172a; letter-spacing: -0.5px;">
                      AI Intelligence Brief
                    </h1>
                  </td>
                  <td align="right" style="vertical-align: bottom;">
                    <div style="font-size: 12px; font-weight: 700; color: #334155;">{date_bn}</div>
                    <div style="font-size: 11px; color: #64748b;">{time_text}</div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Featured Story Section -->
          {f'''
          <tr>
            <td style="padding: 24px 28px 20px 28px; border-bottom: 1px solid #e2e8f0;">
              <div style="border-radius: 12px; overflow: hidden; margin-bottom: 16px; border: 1px solid #f1f5f9;">
                <img src="{featured_img}" alt="{esc(featured.title)}" style="width: 100%; height: auto; max-height: 260px; object-fit: cover; display: block;">
              </div>
              <div style="display: inline-block; padding: 2px 8px; border-radius: 4px; background-color: #fee2e2; color: #dc2626; font-size: 11px; font-weight: 700; margin-bottom: 8px;">
                শীর্ষ খবর &bull; Score {featured.impact_score:.1f}/10
              </div>
              <h2 style="margin: 0 0 10px 0; font-size: 19px; font-weight: 900; line-height: 1.4;">
                <a href="{featured.url}" target="_blank" style="color: #0f172a; text-decoration: none;">
                  {esc(featured.title_bn or featured.title)}
                </a>
              </h2>
              <p style="margin: 0 0 16px 0; font-size: 14px; line-height: 1.6; color: #475569;">
                {esc(clean_summary_text(featured))}
              </p>
              <table role="presentation">
                <tr>
                  <td>
                    <a href="{featured.url}" target="_blank" style="display: inline-block; padding: 10px 18px; border-radius: 8px; background-color: #4f46e5; color: #ffffff; font-size: 13px; font-weight: 700; text-decoration: none;">
                      মূল খবরটি পড়ুন &rarr;
                    </a>
                  </td>
                  <td style="padding-left: 12px; font-size: 12px; color: #64748b;">
                    সোর্স: <strong>{esc(featured.source)}</strong>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          ''' if featured else ''}

          <!-- Secondary Stories List -->
          {f'''
          <tr>
            <td style="padding: 20px 28px 10px 28px;">
              <div style="font-size: 13px; font-weight: 800; color: #0f172a; margin-bottom: 4px;">
                🔬 আরও শীর্ষ AI সংবাদ
              </div>
              {secondary_html}
            </td>
          </tr>
          ''' if secondary_html else ''}

          <!-- Landscape & Trending Box -->
          <tr>
            <td style="padding: 20px 28px; background-color: #f8fafc; border-top: 1px solid #e2e8f0;">
              <table role="presentation" width="100%" style="font-size: 12px; color: #475569;">
                <tr>
                  <td style="vertical-align: top; width: 55%;">
                    <div style="font-weight: 700; color: #0f172a; margin-bottom: 6px;">📊 আজকের AI Landscape</div>
                    <div>🔬 Research: <strong>{research_count}</strong></div>
                    <div>🏢 Industry: <strong>{industry_count}</strong></div>
                    <div>🛠️ Tools & Models: <strong>{tools_count}</strong></div>
                    <div>💼 Business & Community: <strong>{business_count}</strong></div>
                  </td>
                  <td style="vertical-align: top; width: 45%; padding-left: 10px; border-left: 1px solid #e2e8f0;">
                    <div style="font-weight: 700; color: #0f172a; margin-bottom: 6px;">🔥 Trending Topic</div>
                    <div style="font-weight: 600; color: #4f46e5;">{esc(trending_topic)}</div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding: 24px 28px; text-align: center; background-color: #ffffff; border-top: 1px solid #e2e8f0; font-size: 12px; color: #64748b; line-height: 1.6;">
              <p style="margin: 0 0 6px 0; font-weight: 600; color: #0f172a;">
                AI News Monitoring & Daily Digest System
              </p>
              <p style="margin: 0 0 12px 0;">
                স্বয়ংক্রিয় এআই সিস্টেম দ্বারা প্রস্তুতকৃত • প্রতিদিন সকাল ১০:০০ | দুপুর ২:০০ | রাত ৯:০০
              </p>
              <a href="http://localhost:8000" target="_blank" style="display: inline-block; padding: 6px 14px; border-radius: 6px; background-color: #f1f5f9; color: #334155; font-size: 11px; font-weight: 700; text-decoration: none; border: 1px solid #cbd5e1;">
                লাইভ ড্যাশবোর্ড দেখুন &rarr;
              </a>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""
    return html_content

def get_recipient_list() -> List[str]:
    """Extracts a unique, clean list of recipient emails from EMAIL_RECIPIENT or EMAIL_USERNAME."""
    raw = (settings.EMAIL_RECIPIENT or settings.EMAIL_USERNAME or "").strip()
    if not raw:
        return []
    items = re.split(r'[,;\s]+', raw)
    seen = set()
    cleaned = []
    for item in items:
        item = item.strip()
        if item and "@" in item and item.lower() not in seen:
            seen.add(item.lower())
            cleaned.append(item)
    return cleaned

def send_email_sync(subject: str, html_body: str, recipients: List[str]) -> tuple[bool, str, List[str]]:
    """Synchronous SMTP email dispatcher supporting multiple individual recipients."""
    settings.reload_from_env()
    sender = (settings.EMAIL_USERNAME or (recipients[0] if recipients else "")).strip()
    # Google App Passwords often have 4-character spaces like 'xxxx xxxx xxxx xxxx'
    password = settings.EMAIL_PASSWORD.replace(" ", "").strip()
    host = settings.EMAIL_HOST.strip()
    port = settings.EMAIL_PORT

    if not sender or not password or not recipients:
        msg = "Email SMTP credentials or recipient list missing in .env."
        logger.warning(msg)
        return False, msg, []

    sent_successfully = []
    errors = []

    try:
        # Establish connection once for all recipients
        if port == 465:
            server = smtplib.SMTP_SSL(host, port, timeout=25)
        else:
            server = smtplib.SMTP(host, port, timeout=25)
            server.ehlo()
            server.starttls()
            server.ehlo()

        with server:
            server.login(sender, password)
            
            # Send separate email to each recipient to preserve privacy (BCC style)
            for rec in recipients:
                try:
                    msg = MIMEMultipart("alternative")
                    msg["Subject"] = subject
                    msg["From"] = f"AI News Digest <{sender}>"
                    msg["To"] = rec

                    part_html = MIMEText(html_body, "html", "utf-8")
                    msg.attach(part_html)

                    server.sendmail(sender, [rec], msg.as_string())
                    sent_successfully.append(rec)
                    logger.info(f"Email successfully dispatched to {rec}.")
                except Exception as ex:
                    logger.error(f"Failed to send email to {rec}: {ex}")
                    errors.append(f"{rec}: {ex}")

        if sent_successfully:
            return True, f"Sent to {len(sent_successfully)} recipient(s)", sent_successfully
        else:
            return False, "; ".join(errors) or "Failed to send to any recipient", []

    except smtplib.SMTPAuthenticationError as e:
        err_msg = "Gmail Authentication Error: Invalid App Password or Username. Please verify your 16-character Google App Password."
        logger.error(f"{err_msg}: {e}")
        return False, err_msg, []
    except Exception as e:
        logger.error(f"Failed to send email via SMTP: {e}")
        return False, str(e), []

async def dispatch_digest_to_email(items: List[NewsItem], period: str = "manual") -> Dict[str, Any]:
    """Asynchronously prepares and dispatches the HTML newsletter email to all recipients."""
    settings.reload_from_env()
    
    sender = (settings.EMAIL_USERNAME or settings.EMAIL_RECIPIENT).strip()
    recipients = get_recipient_list()
    password = settings.EMAIL_PASSWORD.replace(" ", "").strip()

    if not settings.EMAIL_ENABLED and period != "manual":
        return {"status": "skipped", "reason": "EMAIL_ENABLED is false in .env"}

    if not sender or not password or not recipients:
        return {"status": "skipped", "reason": "Missing EMAIL_USERNAME, EMAIL_PASSWORD or EMAIL_RECIPIENT in .env"}

    now = datetime.now()
    date_str = now.strftime("%d %b %Y")
    
    period_label = "সকালের" if period == "morning" else ("দুপুরের" if period == "afternoon" else ("রাতের" if period == "night" else "বিশেষ"))
    subject = f"🚀 AI Intelligence Brief ({period_label} ডাইজেস্ট) • {date_str}"

    html_content = generate_email_html(items, period=period)

    # Run blocking SMTP in thread pool
    success, reason, sent_list = await asyncio.to_thread(send_email_sync, subject, html_content, recipients)

    if success:
        return {
            "status": "success",
            "recipients": sent_list,
            "recipient_count": len(sent_list),
            "items_sent": len(items[:5])
        }
    else:
        return {"status": "failed", "error": reason}


