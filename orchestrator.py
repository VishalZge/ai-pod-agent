"""
Main Orchestrator
Coordinates all agents in the AI POD system workflow.
"""

import json
import time
import asyncio
from typing import Dict, Any, List
from datetime import datetime
from agents.research_agent import ResearchAgent
from agents.analyzer_agent import AnalyzerAgent
from agents.designer_agent import DesignerAgent
from agents.generation_agent import GenerationAgent
from agents.post_processor_agent import PostProcessorAgent
from agents.pod_agent import PODAgent
from agents.feedback_analyzer import FeedbackAnalyzer
from utils.logger import app_logger, agent_logger
from utils.config import Config


class Orchestrator:
    """Main orchestrator for the AI POD Agent System."""

    def __init__(self):
        """Initialize all agents."""
        self.research_agent = ResearchAgent() if Config.RESEARCH_AGENT_ENABLED else None
        self.analyzer_agent = AnalyzerAgent() if Config.ANALYZER_AGENT_ENABLED else None
        self.designer_agent = DesignerAgent() if Config.DESIGNER_AGENT_ENABLED else None
        self.generation_agent = GenerationAgent() if Config.GENERATION_AGENT_ENABLED else None
        self.post_processor = PostProcessorAgent() if Config.POST_PROCESSOR_ENABLED else None
        self.pod_agent = PODAgent() if Config.POD_UPLOAD_ENABLED else None
        self.feedback_analyzer = FeedbackAnalyzer() if Config.ENABLE_FEEDBACK_LOOP else None

    def run_daily_workflow(self) -> Dict[str, Any]:
        """
        Execute the complete daily workflow.
        Aggressive Mode: Research → Analyze → Design → Generate → Upload → Optimize
        """
        try:
            app_logger.info("=" * 80)
            app_logger.info("STARTING DAILY WORKFLOW - AGGRESSIVE MODE")
            app_logger.info("=" * 80)

            workflow_start = time.time()
            results = {
                "workflow_date": datetime.utcnow().isoformat(),
                "stages": {},
                "total_time_seconds": 0,
            }

            # Stage 1: Research
            if self.research_agent:
                app_logger.info("\n[STAGE 1] RESEARCH AGENT")
                stage_start = time.time()
                trends = self.research_agent.research_trends()
                results["stages"]["research"] = {
                    "status": "completed",
                    "trends_discovered": len(trends),
                    "time_seconds": time.time() - stage_start,
                }
                app_logger.info(f"✓ Research completed: {len(trends)} trends discovered")

            # Stage 2: Analysis & Opportunity Scoring
            if self.analyzer_agent:
                app_logger.info("\n[STAGE 2] ANALYZER AGENT")
                stage_start = time.time()
                opportunities = self.analyzer_agent.analyze_and_score_opportunities()
                results["stages"]["analysis"] = {
                    "status": "completed",
                    "opportunities_scored": len(opportunities),
                    "time_seconds": time.time() - stage_start,
                }
                app_logger.info(f"✓ Analysis completed: {len(opportunities)} opportunities scored")

                # Get top opportunities for generation
                top_opps = self.analyzer_agent.get_top_opportunities_for_generation(limit=Config.BATCH_SIZE)
                app_logger.info(f"✓ Selected {len(top_opps)} top opportunities for generation")
            else:
                top_opps = []

            # Stage 3: Design Creation
            if self.designer_agent and top_opps:
                app_logger.info("\n[STAGE 3] DESIGNER AGENT")
                stage_start = time.time()
                designs = self.designer_agent.create_design_prompts(top_opps)
                results["stages"]["design"] = {
                    "status": "completed",
                    "designs_created": len(designs),
                    "time_seconds": time.time() - stage_start,
                }
                app_logger.info(f"✓ Design creation completed: {len(designs)} unique designs")
            else:
                designs = []

            # Stage 4: Image Generation
            if self.generation_agent and designs:
                app_logger.info("\n[STAGE 4] GENERATION AGENT")
                stage_start = time.time()
                generated_images = self.generation_agent.generate_images_for_designs(designs)
                results["stages"]["generation"] = {
                    "status": "completed",
                    "images_generated": len(generated_images),
                    "time_seconds": time.time() - stage_start,
                }
                app_logger.info(f"✓ Image generation completed: {len(generated_images)} images")
            else:
                generated_images = []

            # Stage 5: Post-Processing (Background Removal)
            if self.post_processor and generated_images:
                app_logger.info("\n[STAGE 5] POST-PROCESSOR AGENT")
                stage_start = time.time()
                image_ids = [img.get("id") for img in generated_images if img.get("id")]
                processed_images = self.post_processor.process_images(image_ids)
                results["stages"]["post_processing"] = {
                    "status": "completed",
                    "images_processed": len(processed_images),
                    "time_seconds": time.time() - stage_start,
                }
                app_logger.info(f"✓ Post-processing completed: {len(processed_images)} images")
            else:
                processed_images = []

            # Stage 6: POD Upload
            if self.pod_agent and processed_images and Config.POD_UPLOAD_ENABLED:
                app_logger.info("\n[STAGE 6] POD UPLOAD AGENT")
                stage_start = time.time()
                image_paths = [img.get("processed_path") for img in processed_images]
                uploaded_products = self.pod_agent.upload_designs(image_paths, {"id": "batch"})
                results["stages"]["pod_upload"] = {
                    "status": "completed",
                    "products_uploaded": len(uploaded_products),
                    "time_seconds": time.time() - stage_start,
                }
                app_logger.info(f"✓ POD upload completed: {len(uploaded_products)} products")
            else:
                app_logger.info("⊘ POD upload disabled (dry-run mode)")

            # Stage 7: Feedback Analysis & Auto-Optimization
            if self.feedback_analyzer and Config.ENABLE_FEEDBACK_LOOP:
                app_logger.info("\n[STAGE 7] FEEDBACK ANALYZER - AUTO-OPTIMIZATION")
                stage_start = time.time()
                optimization_actions = self.feedback_analyzer.analyze_and_optimize()
                results["stages"]["feedback_analysis"] = {
                    "status": "completed",
                    "actions": optimization_actions,
                    "time_seconds": time.time() - stage_start,
                }
                app_logger.info(f"✓ Auto-optimization completed")

            # Final Summary
            results["total_time_seconds"] = time.time() - workflow_start
            results["status"] = "completed"

            app_logger.info("\n" + "=" * 80)
            app_logger.info("DAILY WORKFLOW COMPLETED")
            app_logger.info(f"Total execution time: {results['total_time_seconds']:.2f} seconds")
            app_logger.info("=" * 80)

            return results

        except Exception as e:
            app_logger.error(f"Workflow failed: {str(e)}", exc_info=True)
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def run_continuous(self, interval_hours: int = 24) -> None:
        """Run the workflow continuously at specified intervals."""
        import schedule

        app_logger.info(f"Starting continuous workflow execution every {interval_hours} hours")

        schedule.every(interval_hours).hours.do(self.run_daily_workflow)

        while True:
            schedule.run_pending()
            time.sleep(60)
