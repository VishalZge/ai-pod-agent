"""
Designer Agent
Creates detailed design briefs and prompts using psychology, trends, and art principles.
Uses Gemini to generate optimized prompts for image generation.
"""

import json
from typing import List, Dict, Any
from datetime import datetime
from services.firestore_service import FirestoreService
from services.gemini_service import GeminiService
from services.embedding_service import EmbeddingService
from utils.logger import agent_logger, app_logger
from utils.config import Config


class DesignerAgent:
    """Agent for creating design briefs and prompts."""

    def __init__(self):
        """Initialize designer agent."""
        self.db = FirestoreService()
        self.gemini = GeminiService()
        self.embeddings = EmbeddingService()
        self.name = "DesignerAgent"

    def create_design_prompts(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create 3 design prompt variations per opportunity.
        Each optimized for different product types.
        """
        try:
            agent_logger.info(json.dumps({
                "agent": self.name,
                "action": "create_design_prompts_start",
                "opportunities_count": len(opportunities),
                "timestamp": datetime.utcnow().isoformat()
            }))

            designs = []
            for opportunity in opportunities:
                design_prompts = self._generate_design_variations(opportunity)
                
                for prompt_data in design_prompts:
                    # Check for duplicates
                    existing_designs = [d["description"] for d in designs]
                    is_dup, similarity = self.embeddings.is_duplicate(
                        prompt_data["description"],
                        [{"description": d} for d in existing_designs]
                    )
                    
                    if not is_dup:
                        design_id = self.db.add_design(prompt_data)
                        prompt_data["id"] = design_id
                        designs.append(prompt_data)

            agent_logger.info(json.dumps({
                "agent": self.name,
                "action": "create_design_prompts_complete",
                "designs_created": len(designs),
                "timestamp": datetime.utcnow().isoformat()
            }))

            return designs

        except Exception as e:
            app_logger.error(f"Create design prompts failed: {str(e)}")
            raise

    def _generate_design_variations(self, opportunity: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate 3 design prompt variations for an opportunity.
        Uses psychology, color theory, and current trends.
        """
        try:
            themes = opportunity.get("design_themes", ["trending", "modern"])
            audience = opportunity.get("target_audience", "General audience")
            niche = opportunity.get("recommended_niches", ["general"])[0]

            prompt = f"""
            Create 3 different design prompt variations for a {niche} sticker/print design.
            
            Context:
            - Target Audience: {audience}
            - Design Themes: {', '.join(themes)}
            - Trend Velocity: {opportunity.get('trend_velocity', 'stable')}
            - Market Positioning: {opportunity.get('market_size_estimate', 'medium')} market
            
            For each variation, provide:
            1. A Minimalist/Simple style prompt
            2. An Illustrated/Detailed style prompt  
            3. A Typography/Text-heavy style prompt
            
            Consider:
            - Color psychology for target audience
            - Current design trends (2024)
            - Platform optimization (sticker, t-shirt, mug)
            - Viral/shareable potential
            - Uniqueness vs market familiarity balance
            
            Return JSON:
            {{
                "variations": [
                    {{
                        "style": "style_name",
                        "description": "detailed design prompt",
                        "colors": ["color1", "color2"],
                        "mood": "mood_description",
                        "key_elements": ["element1", "element2"],
                        "psychology": "why this appeals to audience",
                        "product_types": ["sticker", "shirt", "mug"]
                    }}
                ]
            }}
            """

            # Get Gemini-generated designs
            response = self.gemini.generate_text(
                prompt,
                temperature=0.8,
                max_tokens=2048,
                json_mode=True
            )

            try:
                response_data = json.loads(response)
                variations = response_data.get("variations", [])
            except json.JSONDecodeError:
                app_logger.warning("Failed to parse design variations")
                variations = self._default_variations(opportunity)

            # Enhance with metadata
            designs = []
            for i, var in enumerate(variations):
                design = {
                    "opportunity_id": opportunity.get("id"),
                    "theme": opportunity.get("query"),
                    "style": var.get("style", "unknown"),
                    "description": var.get("description", ""),
                    "colors": var.get("colors", []),
                    "mood": var.get("mood", ""),
                    "key_elements": var.get("key_elements", []),
                    "psychology": var.get("psychology", ""),
                    "product_types": var.get("product_types", ["sticker"]),
                    "niche": niche,
                    "target_audience": audience,
                    "variation_index": i,
                    "status": "drafted",
                }
                designs.append(design)

            return designs

        except Exception as e:
            app_logger.error(f"Generate design variations failed: {str(e)}")
            return []

    def _default_variations(self, opportunity: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback variations if Gemini fails."""
        return [
            {
                "style": "Minimalist",
                "description": f"Simple, clean {opportunity.get('query', 'design')} sticker",
                "colors": ["#000000", "#FFFFFF"],
                "mood": "Modern and clean",
                "key_elements": ["simplicity", "clarity"],
                "psychology": "Appeals to minimalist aesthetic lovers",
                "product_types": ["sticker"],
            },
            {
                "style": "Illustrated",
                "description": f"Detailed illustrated {opportunity.get('query', 'design')} artwork",
                "colors": ["#FF6B6B", "#4ECDC4", "#FFE66D"],
                "mood": "Vibrant and artistic",
                "key_elements": ["detail", "color"],
                "psychology": "Attracts artists and creative audiences",
                "product_types": ["sticker", "shirt"],
            },
            {
                "style": "Typography",
                "description": f"Bold typography-based {opportunity.get('query', 'design')} design",
                "colors": ["#1A1A1A", "#FF00FF"],
                "mood": "Bold and statement-making",
                "key_elements": ["text", "boldness"],
                "psychology": "Appeals to those who value messaging",
                "product_types": ["sticker", "shirt", "mug"],
            },
        ]
