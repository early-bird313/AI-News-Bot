import json
import logging
from typing import Dict, Any, Optional
from .config import settings

logger = logging.getLogger(__name__)

# Try importing the official google-genai client
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger.warning("google-genai library not installed or failed to import.")

ANALYSIS_SYSTEM_PROMPT = """
You are an expert AI News Analyst and Tech Journalist.
Your task is to analyze an AI-related news item and provide:
1. title_bn: A compelling, highly readable and clear Bengali headline (বাংলায় আকর্ষণীয় ও সুস্পষ্ট ১-লাইনের মূল শিরোনাম).
2. Impact Score: Float from 1.0 to 10.0 based on real industry significance:
   - 9.0-10.0: Paradigm shift, major frontier foundation model release (e.g., GPT-5, Gemini 2.0 Pro, Claude 3.5 Sonnet, breakthrough open-weights like Llama 4).
   - 7.5-8.9: Major open-source release, breakthrough research paper, major AI chip/hardware milestone.
   - 6.0-7.4: Significant product feature, SDK update, notable acquisition or funding.
   - 1.0-5.9: Minor bugfix, incremental editorial, or niche update.
3. Category: Exactly one of ["LLM", "Research", "Open Source", "Hardware", "Industry", "Tool"].
4. is_trending: Boolean (true if impact score >= 7.5).
5. ai_summary_bn: Exactly 3 concise, clear bullet points in Bengali (বাংলা ভাষা).
   Format each bullet with an emoji indicator:
   • 📌 কী ঘটেছে: [সংক্ষিপ্ত বিবরণ ১ লাইনে]
   • ⚡ গুরুত্ব: [কেন এটি বিশেষ বা প্রযুক্তি দুনিয়ায় কী প্রভাব ফেলবে]
   • 💡 ফলাফল: [ডেভেলপার বা সাধারণ ব্যবহারকারীর কী লাভ হবে]

Return ONLY valid JSON matching this schema:
{
  "title_bn": "বাংলায় চমৎকার ১-লাইনের শিরোনাম",
  "impact_score": 8.5,
  "category": "LLM",
  "is_trending": true,
  "ai_summary_bn": "• 📌 কী ঘটেছে: ...\n• ⚡ গুরুত্ব: ...\n• 💡 ফলাফল: ..."
}
"""

def heuristic_fallback_analysis(title: str, raw_summary: str, default_category: str) -> Dict[str, Any]:
    """Provides an intelligent heuristic analysis when Gemini API is unavailable."""
    title_lower = title.lower()
    score = 5.5
    category = default_category or "Industry"
    
    # High impact keywords
    breakthrough_keywords = ["breakthrough", "state-of-the-art", "sota", "releases", "launches", "gpt-5", "claude", "gemini", "llama", "deepseek", "frontier", "billion parameter"]
    if any(k in title_lower for k in breakthrough_keywords):
        score += 2.5
        
    if "open source" in title_lower or "weights" in title_lower or "hugging face" in title_lower or "github" in title_lower:
        category = "Open Source"
        score += 1.0
    elif "paper" in title_lower or "arxiv" in title_lower or "research" in title_lower or "benchmark" in title_lower:
        category = "Research"
    elif "gpu" in title_lower or "nvidia" in title_lower or "chip" in title_lower or "tpu" in title_lower:
        category = "Hardware"
        score += 1.0
    elif "model" in title_lower or "llm" in title_lower or "reasoning" in title_lower:
        category = "LLM"
        score += 1.0
        
    score = min(9.5, max(4.0, score))
    is_trending = score >= 7.5
    
    # Generate clean Bengali title
    title_bn = f"{title}"
    
    # Simple Bengali summary template
    summary_bn = (
        f"• 📌 ঘটনা: {title}\n"
        f"• ⚡ গুরুত্ব: এআই প্রযুক্তি ও সংশ্লিষ্ট ফিল্ডে এটি একটি গুরুত্বপূর্ণ আপডেট।\n"
        f"• 💡 তথ্য: সোর্স থেকে বিস্তারিত জানার জন্য নিচের লিংকে ক্লিক করুন।"
    )
    
    return {
        "title_bn": title_bn,
        "impact_score": round(score, 1),
        "category": category,
        "is_trending": is_trending,
        "ai_summary_bn": summary_bn
    }

async def analyze_news_item(
    title: str,
    raw_summary: str,
    source_name: str,
    default_category: str = "General AI"
) -> Dict[str, Any]:
    """
    Analyzes an article using Google Gemini Free API (or falls back gracefully).
    """
    api_key = settings.GEMINI_API_KEY
    if not api_key or not GENAI_AVAILABLE:
        return heuristic_fallback_analysis(title, raw_summary, default_category)
        
    try:
        client = genai.Client(api_key=api_key)
        prompt = f"""
Analyze this AI news item:
Title: {title}
Source: {source_name}
Excerpt: {raw_summary[:1000]}
Default Category: {default_category}

Provide your structured JSON response.
"""
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=ANALYSIS_SYSTEM_PROMPT,
                response_mime_type="application/json",
                temperature=0.2,
            )
        )
        
        if response.text:
            data = json.loads(response.text.strip())
            return {
                "title_bn": str(data.get("title_bn", title)).strip(),
                "impact_score": float(data.get("impact_score", 6.0)),
                "category": data.get("category", default_category),
                "is_trending": bool(data.get("is_trending", False)),
                "ai_summary_bn": str(data.get("ai_summary_bn", "")).strip()
            }
    except Exception as e:
        logger.error(f"Gemini API error during news analysis: {e}")
        
    return heuristic_fallback_analysis(title, raw_summary, default_category)
