"""
Generic Product Search Engine
Reusable, configurable search logic for finding products with fuzzy name matching
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Represents a search result with metadata"""
    product_id: str
    product_name: str
    category: str
    subcategory: Optional[str] = None
    price: Optional[float] = None
    sales_frequency: int = 0
    description: str = ""
    match_type: str = "exact"  # exact, concatenated, spaced, partial, individual
    match_score: float = 1.0   # Confidence score for the match


class ProductSearchEngine:
    """
    Generic product search engine that handles fuzzy name matching.
    
    Core Algorithm:
    1. Stage 1: Fast shortlist using first word
    2. Stage 2: Filter by remaining words using multiple combination strategies
    
    This approach is:
    - Fast: Single DB query + in-memory filtering
    - Accurate: Handles various product name formats
    - Scalable: Works for any product naming convention
    - Maintainable: Clear separation of concerns
    """
    
    def __init__(self, neo4j_repo):
        """Initialize with database repository"""
        self.neo4j_repo = neo4j_repo
        
    async def search_products(
        self, 
        product_name: str, 
        category: str,
        limit: int = 10
    ) -> List[SearchResult]:
        """
        Main search method using two-stage algorithm.
        
        Args:
            product_name: Product name to search for (e.g., "Warrior 400 i")
            category: Product category to filter by
            limit: Maximum results to return
            
        Returns:
            List of SearchResult objects sorted by relevance
        """
        try:
            logger.info(f"🔍 Searching for '{product_name}' in category '{category}'")
            
            # Parse search terms
            words = self._parse_search_terms(product_name)
            if not words:
                return []
            
            first_word = words[0]
            other_words = words[1:] if len(words) > 1 else []
            
            # Stage 1: Get shortlist using first word
            shortlist = await self._get_shortlist_by_first_word(first_word, category, limit * 2)
            logger.info(f"📋 Stage 1: Found {len(shortlist)} products containing '{first_word}'")
            
            if not shortlist:
                return []
            
            # Stage 2: Filter by remaining words (if any)
            if other_words:
                filtered_results = self._filter_by_remaining_words(shortlist, other_words, product_name)
                logger.info(f"🎯 Stage 2: Filtered to {len(filtered_results)} matches using words {other_words}")
            else:
                # Single word search - return shortlist as-is
                filtered_results = [(result, "exact", 1.0) for result in shortlist]
            
            # Convert to SearchResult objects
            search_results = []
            for result, match_type, match_score in filtered_results[:limit]:
                search_result = SearchResult(
                    product_id=result["product_id"],
                    product_name=result["product_name"],
                    category=result["category"],
                    subcategory=result.get("subcategory"),
                    price=result.get("price"),
                    sales_frequency=result.get("sales_frequency", 0),
                    description=result.get("description", ""),
                    match_type=match_type,
                    match_score=match_score
                )
                search_results.append(search_result)
            
            logger.info(f"✅ Final: Returning {len(search_results)} search results")
            return search_results
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return []
    
    def _parse_search_terms(self, product_name: str) -> List[str]:
        """Parse and normalize search terms"""
        if not product_name or not product_name.strip():
            return []
        
        # Normalize spaces and convert to lowercase
        clean_name = product_name.strip().lower()
        words = clean_name.split()
        
        # Filter out very short words (but keep numbers)
        filtered_words = [word for word in words if len(word) >= 2 or word.isdigit()]
        
        return filtered_words
    
    async def _get_shortlist_by_first_word(
        self, 
        first_word: str, 
        category: str, 
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Stage 1: Get shortlist using first word search.
        Fast database query to reduce search space.
        """
        query = """
        MATCH (p:Product)
        WHERE p.category = $category
        AND toLower(p.name) CONTAINS toLower($first_word)
        RETURN p.gin as product_id,
               p.name as product_name,
               p.category as category,
               p.subcategory as subcategory,
               p.price as price,
               p.sales_frequency as sales_frequency,
               p.description as description
        ORDER BY p.sales_frequency DESC, p.name ASC
        LIMIT $limit
        """
        
        parameters = {
            "category": category,
            "first_word": first_word,
            "limit": limit
        }
        
        return await self.neo4j_repo.execute_query(query, parameters)
    
    def _filter_by_remaining_words(
        self, 
        shortlist: List[Dict[str, Any]], 
        other_words: List[str], 
        original_query: str
    ) -> List[Tuple[Dict[str, Any], str, float]]:
        """
        Stage 2: Filter shortlist by checking for remaining words in various combinations.
        
        Returns list of tuples: (result, match_type, match_score)
        """
        if not other_words:
            return [(result, "exact", 1.0) for result in shortlist]
        
        filtered_results = []
        
        for result in shortlist:
            product_name = result["product_name"].lower()
            match_info = self._check_word_combinations(product_name, other_words)
            
            if match_info:
                match_type, match_score = match_info
                filtered_results.append((result, match_type, match_score))
                logger.info(f"✅ {match_type.upper()}: '{result['product_name']}' (score: {match_score:.2f})")
        
        # Sort by match score (descending) and sales frequency
        filtered_results.sort(key=lambda x: (x[2], x[0].get("sales_frequency", 0)), reverse=True)
        
        return filtered_results
    
    def _check_word_combinations(
        self, 
        product_name: str, 
        other_words: List[str]
    ) -> Optional[Tuple[str, float]]:
        """
        Check if product name contains the other words in various combinations.
        
        Returns (match_type, match_score) or None if no match.
        
        Match types and priorities:
        1. concatenated: "400i" (highest score)
        2. spaced: "400 i"  
        3. individual: all words present separately
        4. partial: some 2-word combinations present
        """
        
        # 1. Concatenated version (highest priority): "400i"
        concatenated = ''.join(other_words)
        if concatenated in product_name:
            return ("concatenated", 1.0)
        
        # 2. Spaced version: "400 i"
        spaced = ' '.join(other_words)
        if spaced in product_name:
            return ("spaced", 0.9)
        
        # 3. All individual words present: contains both "400" AND "i"
        all_words_present = all(word in product_name for word in other_words)
        if all_words_present:
            return ("individual", 0.8)
        
        # 4. Partial combinations (for 3+ words)
        if len(other_words) >= 2:
            partial_matches = 0
            total_combinations = len(other_words) - 1
            
            for i in range(len(other_words) - 1):
                two_word_combo = ''.join(other_words[i:i+2])
                if two_word_combo in product_name:
                    partial_matches += 1
            
            if partial_matches > 0:
                match_score = 0.6 + (partial_matches / total_combinations) * 0.2  # 0.6-0.8 range
                return ("partial", match_score)
        
        return None


class ProductSearchConfig:
    """Configuration for product search behavior"""
    
    # Default limits
    DEFAULT_SHORTLIST_SIZE = 20
    DEFAULT_RESULT_LIMIT = 10
    
    # Match score thresholds
    MIN_MATCH_SCORE = 0.6
    EXCELLENT_MATCH_SCORE = 0.9
    
    # Logging preferences
    ENABLE_DETAILED_LOGGING = True
    LOG_MATCH_DETAILS = True


# Factory function for easy integration
def create_product_search_engine(neo4j_repo) -> ProductSearchEngine:
    """Factory function to create a configured search engine"""
    return ProductSearchEngine(neo4j_repo)