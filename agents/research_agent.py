"""
Research Agent
Searches the internet for trends, market opportunities, and design gaps.
Uses SerpApi to gather data from multiple sources.
"""

import json
import time
from typing import List, Dict, Any
from datetime import datetime
from services.serpapi_service import SerpApiService
from services.firestore_service import FirestoreService
from services.gemini_service import GeminiService
from utils.logger import agent_logger, app_logger
from utils.config import Config


class ResearchAgent:
    """Agent for market research and trend discovery."""

    def __init__(self):
        """Initialize research agent."""
        self.serpapi = SerpApiService()
        self.db = FirestoreService()
        self.gemini = GeminiService()
        self.name = "ResearchAgent"

    def research_trends(self) -> List[Dict[str, Any]]:
        """
        Comprehensive market research across multiple sources.
        Returns list of discovered trends with scores.
        """
        try:
            agent_logger.info(json.dumps({
                "agent": self.name,
                "action": "research_trends_start",
                "timestamp": datetime.utcnow().isoformat()
            }))

            trends = []
            search_queries = self._generate_search_queries()

            for query in search_queries:
                trend_data = self._search_and_extract_trend(query)
                if trend_data:
                    trends.append(trend_data)
                    trend_id = self.db.add_trend(trend_data)
                    app_logger.info(f"Trend stored: {trend_id}")

            agent_logger.info(json.dumps({
                "agent": self.name,
                "action": "research_trends_complete",
                "trends_found": len(trends),
                "timestamp": datetime.utcnow().isoformat()
            }))

            return trends

        except Exception as e:
            app_logger.error(f"Research trends failed: {str(e)}")
            raise

    def _generate_search_queries(self) -> List[str]:
        """Generate comprehensive search queries for market research."""
        base_queries = [
            "trending sticker designs 2024",
            "best selling print on demand designs",
            "popular niche sticker communities",
            "emerging design trends reddit",
            "sticker market demand analysis",
            "viral design patterns 2024",
            "underserved design niches",
            "design trends etsy bestsellers",
            "niche communities sticker art",
            "print on demand market gaps",
        ]

        # Add category-specific queries
        for category in Config.RESEARCH_CATEGORIES:
            base_queries.extend([
                f"trending {category} sticker designs",
                f"{category} niche sticker market",
                f"best selling {category} designs",
            ])

        return base_queries

    def _search_and_extract_trend(self, query: str) -> Dict[str, Any]:
        """Search for a trend and extract relevant data."""
        try:
            results = self.serpapi.search(query, num_results=20)
            
            if not results:
                return None

            # Extract trend data
            trend_data = {
                "query": query,
                "source_results": results,
                "demand_level": self._calculate_demand(results),
                "competition_level": self._calculate_competition(results),
                "trend_velocity": self._calculate_velocity(results),
                "keywords_extracted": self._extract_keywords(results),
                "market_gaps": self._identify_gaps(results),
                "created_at": datetime.utcnow(),
            }

            return trend_data

        except Exception as e:
            app_logger.warning(f"Trend extraction failed for '{query}': {str(e)}")
            return None

    def _calculate_demand(self, results: List[Dict[str, Any]]) -> int:
        """Calculate demand level (1-10) based on search results."""
        # Simple heuristic: more results = higher demand
        demand = min(10, max(1, len(results) // 2))
        return demand

    def _calculate_competition(self, results: List[Dict[str, Any]]) -> int:
        """Calculate competition level (1-10)."""
        # Check for major competitors mentioned
        major_sites = ["etsy", "redbubble", "teespring", "printful", "amazon"]
        competition_count = 0

        for result in results:
            url = result.get("url", "").lower()
            for site in major_sites:
                if site in url:
                    competition_count += 1

        competition = min(10, max(1, competition_count))
        return competition

    def _calculate_velocity(self, results: List[Dict[str, Any]]) -> str:
        """Determine trend velocity (growing/stable/fading)."""
        # Check date indicators in snippets
        recent_count = 0
        for result in results:
            snippet = result.get("snippet", "").lower()
            if "trending" in snippet or "popular" in snippet or "2024" in snippet:
                recent_count += 1

        if recent_count > len(results) * 0.6:
            return "growing"
        elif recent_count > len(results) * 0.3:
            return "stable"
        else:
            return "fading"

    def _extract_keywords(self, results: List[Dict[str, Any]]) -> List[str]:
        """Extract relevant keywords from search results."""
        keywords = []
        for result in results:
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            text = f"{title} {snippet}".lower()
            
            # Simple keyword extraction
            words = text.split()
            keywords.extend([w for w in words if len(w) > 5])

        # Return top unique keywords
        return list(set(keywords))[:10]

    def _identify_gaps(self, results: List[Dict[str, Any]]) -> List[str]:
        """Identify market gaps and underserved areas."""
        gaps = []
        
        # Check for mentions of unmet needs
        for result in results:
            snippet = result.get("snippet", "").lower()
            if "hard to find" in snippet or "rare" in snippet or "unique" in snippet:
                gaps.append(result.get("title", ""))

        return gaps[:5]

    def research_competitor_landscape(self) -> Dict[str, Any]:
        """Analyze competitor designs and market positioning."""
        try:
            competitors = {
                "etsy": self.serpapi.search("best selling sticker designs etsy", 10),
                "redbubble": self.serpapi.search("trending designs redbubble", 10),
                "printful": self.serpapi.search("printful best products", 10),
            }

            return competitors

        except Exception as e:
            app_logger.error(f"Competitor analysis failed: {str(e)}")
            return {}

    def get_trending_searches(self) -> List[str]:
        """Get current trending searches."""
        try:
            trending = self.serpapi.get_trending_searches()
            return trending[:20]
        except Exception as e:
            app_logger.error(f"Get trending searches failed: {str(e)}")
            return []
