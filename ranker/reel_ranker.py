import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class ReelRanker:
    def __init__(self):
        """Initialize the ReelRanker (OpenAI dependencies removed)."""
        logger.info("ReelRanker initialized (OpenAI functionality removed)")

    def rank_reels(self, query: str, conversation_history: List[Dict[str, str]],
                   reels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank reels based on simple keyword matching (OpenAI removed).
        
        Args:
            query (str): Current user query
            conversation_history (List[Dict]): Previous messages in the conversation
            reels (List[Dict]): List of reels to rank
            
        Returns:
            List[Dict]: Ranked reels with relevance scores
        """
        if not reels:
            return []
        
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        # Simple keyword-based ranking
        ranked_reels = []
        for reel in reels:
            reel_copy = reel.copy()
            relevance_score = 0.0
            
            # Check description
            description = (reel.get('description', '') + ' ' + 
                          reel.get('shortDescription', '') + ' ' +
                          reel.get('longDescription', '')).lower()
            
            # Count matching words
            description_words = set(description.split())
            matches = len(query_words.intersection(description_words))
            relevance_score += matches * 0.1
            
            # Check hashtags
            hashtags = ' '.join(reel.get('hashtags', [])).lower()
            hashtag_words = set(hashtags.split())
            matches = len(query_words.intersection(hashtag_words))
            relevance_score += matches * 0.15
            
            # Check product names
            products = reel.get('products', [])
            for product in products:
                product_name = product.get('name', '').lower()
                product_words = set(product_name.split())
                matches = len(query_words.intersection(product_words))
                relevance_score += matches * 0.2
            
            # Normalize score to 0-1 range
            relevance_score = min(1.0, relevance_score)
            reel_copy["relevance_score"] = relevance_score
            ranked_reels.append(reel_copy)
        
        # Sort reels by relevance score (highest first)
        ranked_reels.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        return ranked_reels
