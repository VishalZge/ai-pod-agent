"""
Generation Agent
Generates high-quality images using Gemini 2.0 Pro image generation.
Uploads to Google Cloud Storage and stores metadata.
"""

import json
import base64
from typing import List, Dict, Any, Optional
from datetime import datetime
from services.firestore_service import FirestoreService
from services.gemini_service import GeminiService
from services.gcs_service import GCSService
from utils.logger import agent_logger, app_logger
from utils.config import Config


class GenerationAgent:
    """Agent for generating high-quality images."""

    def __init__(self):
        """Initialize generation agent."""
        self.db = FirestoreService()
        self.gemini = GeminiService()
        self.gcs = GCSService()
        self.name = "GenerationAgent"
        self.max_concurrent = Config.MAX_CONCURRENT_GENERATIONS

    def generate_images_for_designs(self, designs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate images for all provided designs.
        Aggressive Mode: Generate 3 images per design.
        """
        try:
            agent_logger.info(json.dumps({
                "agent": self.name,
                "action": "generate_images_start",
                "designs_count": len(designs),
                "timestamp": datetime.utcnow().isoformat()
            }))

            generated_images = []
            
            for design in designs:
                images = self._generate_image_variants(design)
                generated_images.extend(images)

            agent_logger.info(json.dumps({
                "agent": self.name,
                "action": "generate_images_complete",
                "images_generated": len(generated_images),
                "timestamp": datetime.utcnow().isoformat()
            }))

            return generated_images

        except Exception as e:
            app_logger.error(f"Generate images failed: {str(e)}")
            raise

    def _generate_image_variants(self, design: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate 3 image variants for a single design.
        Each at high quality 1024x1024.
        """
        try:
            variants = []
            description = design.get("description", "")
            product_types = design.get("product_types", ["sticker"])

            for i in range(Config.IMAGES_PER_OPPORTUNITY):
                # Create variant-specific prompts
                prompt = self._create_generation_prompt(
                    design,
                    variant_index=i,
                    product_type=product_types[i % len(product_types)] if product_types else "sticker"
                )

                # Generate image (placeholder for actual Imagen 3 call)
                image_data = self._call_image_generation(prompt)
                
                if image_data:
                    # Upload to GCS
                    filename = f"{design['id']}_variant_{i}.png"
                    gcs_path = self.gcs.upload_image(
                        image_data,
                        folder="generated_images",
                        filename=filename,
                        metadata={
                            "design_id": design.get("id"),
                            "variant": str(i),
                            "style": design.get("style"),
                            "niche": design.get("niche"),
                        }
                    )

                    # Store metadata in Firestore
                    image_metadata = {
                        "design_id": design.get("id"),
                        "gcs_path": gcs_path,
                        "variant_index": i,
                        "product_type": product_types[i % len(product_types)],
                        "style": design.get("style"),
                        "niche": design.get("niche"),
                        "prompt": prompt,
                        "status": "generated",
                        "quality_score": 0.0,  # Will be set after quality check
                    }

                    image_id = self.db.add_generated_image(image_metadata)
                    image_metadata["id"] = image_id
                    variants.append(image_metadata)

            return variants

        except Exception as e:
            app_logger.error(f"Generate image variants failed: {str(e)}")
            return []

    def _create_generation_prompt(self, design: Dict[str, Any], variant_index: int, product_type: str) -> str:
        """
        Create an optimized prompt for Gemini image generation.
        Includes quality directives and style specifications.
        """
        base_description = design.get("description", "")
        colors = design.get("colors", [])
        mood = design.get("mood", "")
        elements = design.get("key_elements", [])
        style = design.get("style", "Minimalist")

        # Adjust prompt based on variant
        variants_adjustments = [
            "high detail, photorealistic quality",
            "vibrant colors, digital art style",
            "clean vector art, professional design"
        ]

        adjustment = variants_adjustments[variant_index % len(variants_adjustments)]

        # Product-specific optimizations
        product_requirements = {
            "sticker": "clear background, high contrast, easy to cut, vibrant colors",
            "shirt": "bold design, readable from distance, flatlay compatible",
            "mug": "centered design, 1:1 ratio, high contrast",
        }

        product_spec = product_requirements.get(product_type, "")

        prompt = f"""
        Create a stunning {product_type} design with the following specifications:
        
        Design Description: {base_description}
        Style: {style}
        Mood: {mood}
        Key Elements: {', '.join(elements)}
        Color Palette: {', '.join(colors) if colors else 'Modern vibrant colors'}
        
        Quality Requirements:
        - {adjustment}
        - Professional production-ready quality
        - {product_spec}
        - High resolution (1024x1024)
        - Trending 2024 design aesthetic
        
        Generate a visually striking, unique design that:
        ✓ Appeals to target audience
        ✓ Stands out in market
        ✓ Is production-ready
        ✓ Follows current design trends
        """

        return prompt

    def _call_image_generation(self, prompt: str) -> Optional[bytes]:
        """
        Call Gemini image generation API.
        Returns image bytes or None if failed.
        """
        try:
            # This would call actual Imagen 3 API via Gemini
            # For now, returning None as placeholder
            # In production: image_bytes = self.gemini.generate_image(
            #     prompt,
            #     width=Config.IMAGE_WIDTH,
            #     height=Config.IMAGE_HEIGHT,
            # )
            
            app_logger.info(f"Image generation prompt: {prompt[:100]}...")
            return None  # Placeholder

        except Exception as e:
            app_logger.error(f"Image generation failed: {str(e)}")
            return None
