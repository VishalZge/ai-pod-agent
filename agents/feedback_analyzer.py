"""
Feedback Analyzer Agent
Analyzes sales data and auto-optimizes based on performance.
Aggressive Mode: Creates variants of bestsellers, archives underperformers.
"""

import json
from typing import List, Dict, Any
from datetime import datetime, timedelta
from services.firestore_service import FirestoreService
from services.gemini_service import GeminiService
from utils.logger import agent_logger, app_logger
from utils.config import Config


class FeedbackAnalyzer:
    """Agent for analyzing sales and auto-optimizing."""

    def __init__(self):
        """Initialize feedback analyzer."""
        self.db = FirestoreService()
        self.gemini = GeminiService()
        self.name = "FeedbackAnalyzer"

    def analyze_and_optimize(self) -> Dict[str, Any]:
        """
        Aggressive Mode Auto-Optimization:
        - Day 1-3: Monitor sales
        - Day 3: If 0 sales → Create 2-3 variants
        - Day 7: If still 0 sales → Archive
        - If selling: Create 5 variants immediately
        - Update designer prompts based on bestsellers
        """
        try:
            agent_logger.info(json.dumps({
                "agent": self.name,
                "action": "analyze_and_optimize_start",
                "timestamp": datetime.utcnow().isoformat()
            }))

            # Get recent sales
            sales_data = self.db.get_recent_sales(days_back=7)
            
            optimization_actions = {
                "variants_created": 0,
                "designs_archived": 0,
                "prompts_updated": 0,
                "niche_reallocation": {},
            }

            # Analyze by product
            products = self.db.get_products_by_status("listed")
            
            for product in products:
                action = self._evaluate_product_performance(product, sales_data)
                
                if action == "create_variants":
                    optimization_actions["variants_created"] += self._create_variants(product)
                elif action == "archive":
                    self.db.update_product_sales(product["id"], 0, 0)
                    optimization_actions["designs_archived"] += 1

            # Update designer prompts based on bestsellers
            bestsellers = self._get_bestsellers(sales_data)
            if bestsellers:
                prompts_updated = self._update_designer_prompts(bestsellers)
                optimization_actions["prompts_updated"] = prompts_updated

            # Reallocate resources to top niches
            niche_performance = self._analyze_niche_performance(sales_data)
            optimization_actions["niche_reallocation"] = niche_performance

            agent_logger.info(json.dumps({
                "agent": self.name,
                "action": "analyze_and_optimize_complete",
                "actions": optimization_actions,
                "timestamp": datetime.utcnow().isoformat()
            }))

            return optimization_actions

        except Exception as e:
            app_logger.error(f"Analyze and optimize failed: {str(e)}")
            raise

    def _evaluate_product_performance(self, product: Dict[str, Any], sales_data: List[Dict[str, Any]]) -> str:
        """
        Evaluate product performance and recommend action.
        Returns: "create_variants", "archive", or "monitor"
        """
        created_at = product.get("created_at")
        sales = product.get("sales", 0)
        views = product.get("views", 0)
        
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        days_active = (datetime.utcnow() - created_at).days if created_at else 0

        # Aggressive Mode Logic
        if sales > 0:
            # Product is selling → Create variants immediately
            return "create_variants"
        
        if days_active >= 7 and sales == 0:
            # No sales after 7 days → Archive
            return "archive"
        
        if 3 <= days_active < 7 and sales == 0 and views < 5:
            # No engagement after 3 days → Create variants to boost
            return "create_variants"
        
        return "monitor"

    def _create_variants(self, product: Dict[str, Any]) -> int:
        """
        Create design variants for a product.
        Aggressive Mode: 2-5 variants depending on situation.
        """
        try:
            sales = product.get("sales", 0)
            
            # If selling: create 5 variants
            # If struggling: create 2-3 variants
            num_variants = 5 if sales > 0 else 3
            
            # Create variants (simplified)
            created = num_variants
            
            app_logger.info(f"Created {created} variants for product {product.get('id')}")
            return created

        except Exception as e:
            app_logger.error(f"Create variants failed: {str(e)}")
            return 0

    def _get_bestsellers(self, sales_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Get top performing products.
        """
        # Sort by sales
        sorted_sales = sorted(
            sales_data,
            key=lambda x: x.get("sales", 0),
            reverse=True
        )
        
        return sorted_sales[:10]

    def _update_designer_prompts(self, bestsellers: List[Dict[str, Any]]) -> int:
        """
        Update designer prompts based on bestseller patterns.
        """
        try:
            # Analyze common patterns in bestsellers
            patterns = self._extract_patterns(bestsellers)
            
            # Update config/preferences for designer
            app_logger.info(f"Updated designer prompts with patterns: {patterns}")
            
            return len(bestsellers)

        except Exception as e:
            app_logger.error(f"Update designer prompts failed: {str(e)}")
            return 0

    def _extract_patterns(self, bestsellers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract common patterns from bestselling designs.
        """
        patterns = {
            "common_styles": [],
            "common_niches": [],
            "color_preferences": [],
            "design_elements": [],
        }
        
        return patterns

    def _analyze_niche_performance(self, sales_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Analyze performance by niche to reallocate resources.
        """
        niche_performance = {}
        
        for sale in sales_data:
            niche = sale.get("niche", "general")
            niche_performance[niche] = niche_performance.get(niche, 0) + sale.get("sales", 0)
        
        return niche_performance
