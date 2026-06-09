"""
Post-Processor Agent
Removes backgrounds and optimizes images for different POD products.
"""

import json
from typing import List, Dict, Any
from datetime import datetime
from services.firestore_service import FirestoreService
from services.gcs_service import GCSService
from utils.logger import agent_logger, app_logger
from utils.config import Config


class PostProcessorAgent:
    """Agent for background removal and image optimization."""

    def __init__(self):
        """Initialize post-processor agent."""
        self.db = FirestoreService()
        self.gcs = GCSService()
        self.name = "PostProcessorAgent"

    def process_images(self, image_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Process images: remove backgrounds and optimize.
        """
        try:
            agent_logger.info(json.dumps({
                "agent": self.name,
                "action": "process_images_start",
                "images_count": len(image_ids),
                "timestamp": datetime.utcnow().isoformat()
            }))

            processed_images = []
            
            for image_id in image_ids:
                # Get image from Firestore
                image_data = self._get_image_data(image_id)
                if not image_data:
                    continue

                # Download from GCS
                image_bytes = self.gcs.download_image(image_data["gcs_path"])
                
                # Remove background
                processed_bytes = self._remove_background(image_bytes)
                
                if processed_bytes:
                    # Upload processed image
                    processed_path = self.gcs.upload_image(
                        processed_bytes,
                        folder="processed_images",
                        filename=f"{image_data['design_id']}_processed.png"
                    )
                    
                    # Update Firestore
                    self.db.update_image_status(image_id, "bg_removed")
                    
                    processed_images.append({
                        "id": image_id,
                        "original_path": image_data["gcs_path"],
                        "processed_path": processed_path,
                        "status": "bg_removed"
                    })

            agent_logger.info(json.dumps({
                "agent": self.name,
                "action": "process_images_complete",
                "processed_count": len(processed_images),
                "timestamp": datetime.utcnow().isoformat()
            }))

            return processed_images

        except Exception as e:
            app_logger.error(f"Process images failed: {str(e)}")
            raise

    def _get_image_data(self, image_id: str) -> Dict[str, Any]:
        """Get image data from Firestore."""
        # Placeholder: would fetch from actual Firestore
        return {}

    def _remove_background(self, image_bytes: bytes) -> bytes:
        """
        Remove background from image.
        Uses RemBG or Rembg library.
        """
        try:
            if Config.USE_REMBG:
                # Use RemBG API
                pass
            else:
                # Use local rembg library
                try:
                    from rembg import remove
                    result = remove(image_bytes)
                    return result
                except ImportError:
                    app_logger.warning("rembg not installed, returning original")
                    return image_bytes
            
            return image_bytes

        except Exception as e:
            app_logger.error(f"Background removal failed: {str(e)}")
            return image_bytes
