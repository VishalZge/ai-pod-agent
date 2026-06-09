"""
POD Upload Agent
Handles uploading designs to Print-on-Demand platforms.
Supports Printful, Redbubble, and others.
"""

import json
import requests
from typing import List, Dict, Any
from datetime import datetime
from services.firestore_service import FirestoreService
from utils.logger import agent_logger, app_logger
from utils.config import Config


class PODAgent:
    """Agent for uploading to POD platforms."""

    def __init__(self):
        """Initialize POD agent."""
        self.db = FirestoreService()
        self.name = "PODAgent"
        self.platforms = {
            "printful": {"base_url": "https://api.printful.com", "key": Config.PRINTFUL_API_KEY},
            "redbubble": {"base_url": "https://api.redbubble.com", "key": Config.REDBUBBLE_API_KEY},
        }

    def upload_designs(self, image_paths: List[str], design_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Upload designs to POD platforms.
        """
        try:
            agent_logger.info(json.dumps({
                "agent": self.name,
                "action": "upload_designs_start",
                "images_count": len(image_paths),
                "timestamp": datetime.utcnow().isoformat()
            }))

            uploaded_products = []

            for platform in self.platforms.keys():
                if not Config.POD_UPLOAD_ENABLED:
                    app_logger.info(f"POD upload disabled for {platform}")
                    continue

                products = self._upload_to_platform(platform, image_paths, design_data)
                uploaded_products.extend(products)

            agent_logger.info(json.dumps({
                "agent": self.name,
                "action": "upload_designs_complete",
                "products_uploaded": len(uploaded_products),
                "timestamp": datetime.utcnow().isoformat()
            }))

            return uploaded_products

        except Exception as e:
            app_logger.error(f"Upload designs failed: {str(e)}")
            raise

    def _upload_to_platform(self, platform: str, image_paths: List[str], design_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Upload to specific platform.
        """
        try:
            products = []
            
            for image_path in image_paths:
                # Platform-specific upload logic
                if platform == "printful":
                    product = self._upload_to_printful(image_path, design_data)
                elif platform == "redbubble":
                    product = self._upload_to_redbubble(image_path, design_data)
                else:
                    continue

                if product:
                    # Store in Firestore
                    product_id = self.db.add_product(product)
                    product["id"] = product_id
                    products.append(product)

            return products

        except Exception as e:
            app_logger.error(f"Upload to {platform} failed: {str(e)}")
            return []

    def _upload_to_printful(self, image_path: str, design_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upload to Printful API.
        """
        try:
            # Placeholder for actual Printful API call
            return {
                "platform": "printful",
                "product_type": "sticker",
                "design_id": design_data.get("id"),
                "image_url": image_path,
                "title": design_data.get("theme", "Design"),
                "status": "listed",
            }
        except Exception as e:
            app_logger.error(f"Printful upload failed: {str(e)}")
            return None

    def _upload_to_redbubble(self, image_path: str, design_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upload to Redbubble API.
        """
        try:
            # Placeholder for actual Redbubble API call
            return {
                "platform": "redbubble",
                "product_type": "sticker",
                "design_id": design_data.get("id"),
                "image_url": image_path,
                "title": design_data.get("theme", "Design"),
                "status": "listed",
            }
        except Exception as e:
            app_logger.error(f"Redbubble upload failed: {str(e)}")
            return None
