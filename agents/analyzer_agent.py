"""
Analyzer Agent
Analyzes research data to identify opportunities and score them for design generation.
Uses Gemini to perform intelligent analysis and ranking.
"""

import json
from typing import List, Dict, Any
from datetime import datetime
from services.firestore_service import FirestoreService
from services.gemini_service import GeminiService
from utils.logger import agent_logger, app_logger
from utils.config import Config


class AnalyzerAgent:
    """Agent for analyzing trends and scoring opportunities."""

    def __init__(self):
        """Initialize analyzer agent."""
        self.db = FirestoreService()
        self.gemini = GeminiService()
        self.name = "AnalyzerAgent"

    def analyze_and_score_opportunities(self) -> List[Dict[str, Any]]:
        """
        Analyze all trends and identify top opportunities for design generation.
        Returns sorted list of opportunities with scores.
        """
        try:
            agent_logger.info(json.dumps({
                "agent": self.name,
                "action": "analyze_opportunities_start",
                "timestamp": datetime.utcnow().isoformat()
            }))

            # Get recent trends
            trends = self.db.get_trending_niches(limit=50)
            
            if not trends:
                app_logger.warning("No trends found for analysis")
                return []

            opportunities = []
            for trend in trends:
                opportunity = self._score_opportunity(trend)
                if opportunity:
                    opportunities.append(opportunity)
                    opp_id = self.db.add_opportunity(opportunity)
                    app_logger.info(f"Opportunity stored: {opp_id} with score {opportunity['opportunity_score']}")

            # Sort by score (descending)
            opportunities.sort(key=lambda x: x["opportunity_score"], reverse=True)

            agent_logger.info(json.dumps({
                "agent": self.name,
                "action": "analyze_opportunities_complete",
                "opportunities_found": len(opportunities),
                "top_score": opportunities[0]["opportunity_score"] if opportunities else 0,
                "timestamp": datetime.utcnow().isoformat()
            }))

            return opportunities[:20]  # Return top 20

        except Exception as e:
            app_logger.error(f"Analyze opportunities failed: {str(e)}")
            raise

    def _score_opportunity(self, trend: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score a single opportunity using Gemini analysis.
        Returns opportunity dict with comprehensive scoring.
        """
        try:
            # Prepare analysis prompt
            analysis_prompt = f"""
            Analyze this design opportunity and provide structured scoring:
            
            Trend Query: {trend.get('query', '')}
            Demand Level: {trend.get('demand_level', 0)}/10
            Competition Level: {trend.get('competition_level', 0)}/10
            Trend Velocity: {trend.get('trend_velocity', 'unknown')}
            Keywords: {', '.join(trend.get('keywords_extracted', [])[:5])}
            Market Gaps: {', '.join(trend.get('market_gaps', [])[:3])}
            
            Provide JSON response with:
            {{
                "demand_score": 0-10,
                "competition_score": 0-10,
                "profit_potential": 0-10,
                "uniqueness_score": 0-10,
                "market_size_estimate": "small/medium/large",
                "target_audience": "description",
                "design_themes": ["theme1", "theme2"],
                "recommended_niches": ["niche1", "niche2"],
                "risk_level": "low/medium/high",
                "time_to_market": "days",
                "final_opportunity_score": 0-100
            }}
            """

            # Get Gemini analysis
            analysis_response = self.gemini.generate_text(
                analysis_prompt,
                temperature=0.5,
                max_tokens=1024,
                json_mode=True
            )

            try:
                analysis = json.loads(analysis_response)
            except json.JSONDecodeError:
                app_logger.warning("Failed to parse Gemini response, using defaults")
                analysis = self._default_scoring(trend)

            # Create opportunity object
            opportunity = {
                "trend_id": trend.get("id"),
                "query": trend.get("query"),
                **analysis,
                "status": "pending",
                "created_at": datetime.utcnow(),
            }

            return opportunity

        except Exception as e:
            app_logger.error(f"Score opportunity failed: {str(e)}")
            return None

    def _default_scoring(self, trend: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback scoring if Gemini analysis fails."""
        demand = trend.get("demand_level", 5)
        competition = 10 - trend.get("competition_level", 5)
        
        return {
            "demand_score": demand,
            "competition_score": competition,
            "profit_potential": (demand + competition) // 2,
            "uniqueness_score": competition * 0.8,
            "market_size_estimate": "medium",
            "target_audience": "General audience",
            "design_themes": trend.get("keywords_extracted", [])[:3],
            "recommended_niches": Config.RESEARCH_CATEGORIES[:3],
            "risk_level": "medium",
            "time_to_market": 1,
            "final_opportunity_score": min(100, (demand * 2 + competition * 1.5) / 3.5),
        }

    def get_top_opportunities_for_generation(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top opportunities ready for design generation.
        Aggressive Mode: Selects top N daily opportunities.
        """
        try:
            opportunities = self.db.get_top_opportunities(limit=limit)
            
            # Mark as in_progress
            for opp in opportunities:
                self.db.update_opportunity_status(opp["id"], "in_progress")

            agent_logger.info(json.dumps({
                "agent": self.name,
                "action": "select_top_opportunities",
                "count": len(opportunities),
                "timestamp": datetime.utcnow().isoformat()
            }))

            return opportunities

        except Exception as e:
            app_logger.error(f"Get top opportunities failed: {str(e)}")
            return []
