from typing import List, Dict

SOURCES: List[Dict[str, str]] = [
    # Official AI Labs
    {
        "id": "openai",
        "name": "OpenAI Blog",
        "url": "https://openai.com/news/rss.xml",
        "type": "rss",
        "default_category": "LLM",
    },
    {
        "id": "deepmind",
        "name": "Google DeepMind",
        "url": "https://deepmind.google/blog/rss.xml",
        "type": "rss",
        "default_category": "Research",
    },
    {
        "id": "huggingface",
        "name": "Hugging Face",
        "url": "https://huggingface.co/blog/feed.xml",
        "type": "rss",
        "default_category": "Open Source",
    },
    {
        "id": "mit_tech_review",
        "name": "MIT Tech Review AI",
        "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
        "type": "rss",
        "default_category": "Research",
    },
    
    # Tech Media
    {
        "id": "techcrunch_ai",
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "type": "rss",
        "default_category": "Industry",
    },
    {
        "id": "venturebeat_ai",
        "name": "VentureBeat AI",
        "url": "https://venturebeat.com/category/ai/feed/",
        "type": "rss",
        "default_category": "Industry",
    },
    {
        "id": "arstechnica_ai",
        "name": "Ars Technica AI",
        "url": "https://arstechnica.com/tag/ai/feed/",
        "type": "rss",
        "default_category": "Tech News",
    },
    {
        "id": "theverge_ai",
        "name": "The Verge AI",
        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "type": "rss",
        "default_category": "Tech News",
    },

    # Research Papers
    {
        "id": "arxiv_ai",
        "name": "ArXiv cs.AI",
        "url": "https://rss.arxiv.org/rss/cs.AI",
        "type": "rss",
        "default_category": "Research",
    },
    {
        "id": "arxiv_lg",
        "name": "ArXiv cs.LG",
        "url": "https://rss.arxiv.org/rss/cs.LG",
        "type": "rss",
        "default_category": "Research",
    },

    # Community Discussions
    {
        "id": "reddit_localllama",
        "name": "Reddit r/LocalLLaMA",
        "url": "https://www.reddit.com/r/LocalLLaMA/top/.rss?t=day",
        "type": "rss",
        "default_category": "Open Source",
    },
    {
        "id": "reddit_ml",
        "name": "Reddit r/MachineLearning",
        "url": "https://www.reddit.com/r/MachineLearning/top/.rss?t=day",
        "type": "rss",
        "default_category": "Research",
    },
    {
        "id": "hackernews_ai",
        "name": "Hacker News AI",
        "url": "https://hacker-news.firebaseio.com/v0/",
        "type": "hackernews",
        "default_category": "Community",
    }
]
