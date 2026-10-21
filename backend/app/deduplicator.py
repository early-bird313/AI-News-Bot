import re
import hashlib
from typing import Tuple, Optional, List, Dict, Any
from rapidfuzz import fuzz

# Common stop phrases and outlet suffixes in news titles
SUFFIXES = [
    r"\|\s*TechCrunch.*$",
    r"-\s*VentureBeat.*$",
    r"\|\s*The Verge.*$",
    r"-\s*Ars Technica.*$",
    r"\|\s*MIT Technology Review.*$",
    r"-\s*OpenAI.*$",
    r"\|\s*Reuters.*$",
    r"-\s*Bloomberg.*$"
]

STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "with",
    "by", "from", "of", "about", "into", "through", "after", "is", "are", "was",
    "were", "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "will", "would", "shall", "should", "may", "might", "must", "can", "could",
    "its", "it", "this", "that", "these", "those", "new", "announces", "introduces"
}

def clean_title(title: str) -> str:
    """Removes outlet suffixes, brackets, and extra punctuation."""
    t = title
    for suffix in SUFFIXES:
        t = re.sub(suffix, "", t, flags=re.IGNORECASE)
    # Remove bracketed tags like [R], [D], [P] often found on Reddit/ArXiv
    t = re.sub(r"^\[[A-Za-z0-9_\-\s]+\]\s*", "", t)
    # Remove special characters
    t = re.sub(r"[^\w\s]", " ", t)
    # Normalize whitespace
    return " ".join(t.split()).strip()

def normalize_title(title: str) -> str:
    """Lowercases, cleans, and strips common stop words for high-accuracy deduplication."""
    cleaned = clean_title(title).lower()
    tokens = [w for w in cleaned.split() if w not in STOP_WORDS and len(w) > 1]
    return " ".join(tokens)

def compute_title_hash(title: str) -> str:
    norm = normalize_title(title)
    return hashlib.md5(norm.encode("utf-8")).hexdigest()

def is_duplicate_story(
    candidate_title: str,
    recent_items: List[Dict[str, Any]],
    similarity_threshold: float = 78.0
) -> Tuple[bool, Optional[Dict[str, Any]], float]:
    """
    Checks if a news story covers the exact same event as any recent article (within 48 hours).
    Strictly keeps only the earliest/best source and rejects duplicate reports.
    """
    candidate_norm = normalize_title(candidate_title)
    candidate_clean = clean_title(candidate_title).lower()
    
    if not candidate_norm:
        return False, None, 0.0
    
    candidate_hash = compute_title_hash(candidate_title)
    
    for item in recent_items:
        # Fast path 1: identical hash
        if item.get("title_hash") == candidate_hash:
            return True, item, 100.0
            
        existing_title = item.get("title", "")
        existing_norm = item.get("normalized_title") or normalize_title(existing_title)
        existing_clean = clean_title(existing_title).lower()
        
        # Token sort ratio accounts for reordered headlines like:
        # "OpenAI launches GPT-5 with reasoning" vs "GPT-5 launched by OpenAI with reasoning"
        sort_ratio = fuzz.token_sort_ratio(candidate_norm, existing_norm)
        set_ratio = fuzz.token_set_ratio(candidate_clean, existing_clean)
        
        score = max(sort_ratio, set_ratio * 0.95)
        
        if score >= similarity_threshold:
            return True, item, score
            
    return False, None, 0.0
