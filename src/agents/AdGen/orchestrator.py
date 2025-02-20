import os
import json
from datetime import datetime
from typing import Dict, List, Optional

from langchain.chat_models import AzureChatOpenAI
from langchain.agents import AgentExecutor

from .ad_content_generator import CreativeAgent
from .image_gen import SDXLTurboGenerator
from .graph import build_graph
from .types import GraphState, StrategyAnalysis, CampaignIdeas

class AdCampaignOrchestrator:
    """
    Orchestrates the complete ad campaign generation workflow using LangGraph.
    """
    def __init__(
        self,
        creative_agent: CreativeAgent,
        image_generator: SDXLTurboGenerator,
        llm: Optional[AzureChatOpenAI] = None,
        agent_executor: Optional[AgentExecutor] = None
    ):
        """
        Initialize the orchestrator.
        
        Args:
            creative_agent: Initialized CreativeAgent instance
            image_generator: Initialized SDXLTurboGenerator instance
            llm: Optional language model instance
            agent_executor: Optional agent executor instance
        """
        self.creative_agent = creative_agent
        self.image_generator = image_generator
        self.llm = llm or creative_agent.llm
        self.agent_executor = agent_executor
        
        # Use absolute path for output directory
        self.output_dir = os.path.abspath("Outputs")

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize the filename to be safe for all operating systems."""
        sanitized = "".join(c if c.isalnum() else "_" for c in filename)
        return sanitized.strip("_")

    def _create_campaign_directory(self, campaign_name: str) -> str:
        """Create a directory for the campaign assets."""
        sanitized_name = self._sanitize_filename(campaign_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        campaign_dir = os.path.join(self.output_dir, f"{sanitized_name}_{timestamp}")
        
        campaign_dir = os.path.abspath(campaign_dir)
        os.makedirs(campaign_dir, exist_ok=True)
        print(f"Created campaign directory at: {campaign_dir}")
        return campaign_dir

    def _save_text_asset(self, campaign_dir: str, filename: str, content: str) -> str:
        """Save a text asset to the campaign directory."""
        file_path = os.path.join(campaign_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path

    async def _save_campaign_assets(self, campaign_dir: str, assets: Dict) -> Dict:
        """Save generated campaign assets to files."""
        # Save tagline
        tagline_path = self._save_text_asset(
            campaign_dir,
            'tagline.txt',
            assets['tagline']
        )
        
        # Save story
        story_path = self._save_text_asset(
            campaign_dir,
            'story.txt',
            assets['story']
        )
        
        # Generate and save image
        image_path = self.image_generator.generate_image(
            assets['image_prompt'],
            output_dir=campaign_dir
        )
        
        # Save quality check results if available
        if 'quality_check' in assets:
            quality_check_path = self._save_text_asset(
                campaign_dir,
                'quality_check.txt',
                assets['quality_check']
            )
        
        return {
            'tagline': tagline_path,
            'story': story_path,
            'image': image_path,
            'quality_check': quality_check_path if 'quality_check' in assets else None
        }

    async def generate_campaign(
        self,
        brand_info: str,
        target_audience: str,
        campaign_goals: str,
        campaign_ideas: List[CampaignIdeas]
    ) -> List[Dict]:
        """
        Generate complete ad campaigns using the enhanced workflow.
        
        Args:
            brand_info: Information about the brand
            target_audience: Target audience description
            campaign_goals: Campaign objectives
            campaign_ideas: List of campaign ideas to process
            
        Returns:
            List[Dict]: List of generated campaigns with asset paths
        """
        # Create main output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize workflow graph
        workflow = await build_graph(self.llm, self.agent_executor)
        
        # Prepare initial state
        initial_state: GraphState = {
            "strategy_analysis": {
                "brand_info": brand_info,
                "target_audience": target_audience,
                "campaign_goals": campaign_goals
            },
            "campaign_ideas": campaign_ideas,
            "creative_direction": {},
            "campaign_assets": []
        }
        
        # Run workflow
        final_state = await workflow.ainvoke(initial_state)
        
        # Process and save results
        results = []
        for idx, assets in enumerate(final_state["campaign_assets"]):
            campaign_name = campaign_ideas[idx]["campaign_name"]
            campaign_dir = self._create_campaign_directory(campaign_name)
            
            # Save assets to files
            asset_paths = await self._save_campaign_assets(campaign_dir, assets)
            
            # Save campaign details
            campaign_details = {
                **campaign_ideas[idx],
                "strategy_analysis": final_state["strategy_analysis"],
                "creative_direction": final_state["creative_direction"],
                "generated_assets": {
                    **asset_paths,
                    "tagline_content": assets["tagline"],
                    "story_content": assets["story"],
                    "image_prompt": assets["image_prompt"],
                    "quality_check": assets.get("quality_check")
                }
            }
            
            details_path = self._save_text_asset(
                campaign_dir,
                'campaign_details.json',
                json.dumps(campaign_details, indent=2)
            )
            
            results.append({
                'campaign_name': campaign_name,
                'campaign_dir': campaign_dir,
                'assets': {
                    **asset_paths,
                    'details': details_path
                }
            })
        
        return results

    async def generate_single_campaign(self, campaign: CampaignIdeas) -> Dict:
        """
        Generate assets for a single campaign using the enhanced workflow.
        
        Args:
            campaign: Campaign details
            
        Returns:
            Dict: Generated campaign with asset paths
        """
        results = await self.generate_campaign(
            brand_info=campaign.get("brand_info", ""),
            target_audience=campaign.get("target_audience", ""),
            campaign_goals=campaign.get("campaign_goals", ""),
            campaign_ideas=[campaign]
        )
        
        return results[0] if results else None
