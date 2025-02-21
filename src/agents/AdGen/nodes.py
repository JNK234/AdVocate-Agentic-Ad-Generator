from typing import Dict, Any, List
from langchain.chat_models import AzureChatOpenAI
from langchain.agents import AgentExecutor
from .prompts import (
    STRATEGY_ANALYSIS_PROMPT,
    CREATIVE_DIRECTION_PROMPT,
    TAGLINE_GENERATION_PROMPT,
    STORY_GENERATION_PROMPT,
    IMAGE_PROMPT_GENERATION,
    QUALITY_CHECK_PROMPT
)
from .types import (
    GraphState,
    StrategyAnalysis,
    CreativeDirection,
    CampaignAssets,
    CampaignIdeas
)

class GraphNodes:
    """
    Nodes for the AdGen workflow graph.
    """
    def __init__(self, llm: AzureChatOpenAI, agent_executor: AgentExecutor):
        self.llm = llm
        self.agent_executor = agent_executor

    async def analyze_strategy(self, state: GraphState) -> GraphState:
        """Analyze campaign strategy based on input parameters."""
        strategy_analysis = await self.llm.apredict_messages(
            STRATEGY_ANALYSIS_PROMPT.format_messages(
                brand_info=state["strategy_analysis"]["brand_info"],
                target_audience=state["strategy_analysis"]["target_audience"],
                campaign_goals=state["strategy_analysis"]["campaign_goals"]
            )
        )
        
        state["strategy_analysis"] = {
            "analysis": strategy_analysis.content,
            **state["strategy_analysis"]
        }
        return state

    async def generate_creative_direction(self, state: GraphState) -> GraphState:
        """Generate creative direction based on strategy analysis."""
        creative_direction = await self.llm.apredict_messages(
            CREATIVE_DIRECTION_PROMPT.format_messages(
                strategy_analysis=state["strategy_analysis"]["analysis"]
            )
        )
        
        state["creative_direction"] = {
            "direction": creative_direction.content,
            **state.get("creative_direction", {})
        }
        return state

    async def generate_campaign_assets(self, state: GraphState) -> GraphState:
        """Generate campaign assets based on creative direction."""
        campaign_ideas = state.get("campaign_ideas", [])
        assets = []

        for idea in campaign_ideas:
            # Generate tagline
            tagline_response = await self.llm.apredict_messages(
                TAGLINE_GENERATION_PROMPT.format_messages(
                    core_message=idea["core_message"],
                    visual_theme=idea["visual_theme_description"],
                    emotional_appeal=idea["key_emotional_appeal"]
                )
            )

            # Generate story
            story_response = await self.llm.apredict_messages(
                STORY_GENERATION_PROMPT.format_messages(
                    core_message=idea["core_message"],
                    visual_theme=idea["visual_theme_description"],
                    emotional_appeal=idea["key_emotional_appeal"]
                )
            )

            # Truncate prompt components
            def truncate_text(text: str, max_length: int = 500) -> str:
                """Truncate text to specified length while keeping complete sentences."""
                if not text or len(text) <= max_length:
                    return text
                
                # Find the last complete sentence within the limit
                truncated = text[:max_length]
                last_period = truncated.rfind('.')
                if last_period > 0:
                    return text[:last_period + 1]
                return truncated
            
            # Generate image prompt with truncated components
            campaign_name = truncate_text(idea["campaign_name"], 100)
            product_prompt = truncate_text(idea["prompt_suggestions"].get("product_focused", ""), 400)
            brand_prompt = truncate_text(idea["prompt_suggestions"].get("brand_focused", ""), 400)
            social_prompt = truncate_text(idea["prompt_suggestions"].get("social_media", ""), 400)
            
            # Create a concise summary prompt
            summary_prompt = f"{campaign_name}: {idea['core_message']}"
            summary_prompt = truncate_text(summary_prompt, 200)
            
            image_prompt_response = await self.llm.apredict_messages(
                IMAGE_PROMPT_GENERATION.format_messages(
                    campaign_name=campaign_name,
                    product_prompt=product_prompt,
                    brand_prompt=brand_prompt,
                    social_prompt=social_prompt,
                    summary_prompt=summary_prompt
                )
            )

            assets.append({
                "tagline": tagline_response.content,
                "story": story_response.content,
                "image_prompt": image_prompt_response.content
            })

        state["campaign_assets"] = assets
        return state

    async def quality_check(self, state: GraphState) -> GraphState:
        """Perform quality check on generated assets."""
        assets = state.get("campaign_assets", [])
        checked_assets = []

        for asset in assets:
            quality_check_response = await self.llm.apredict_messages(
                QUALITY_CHECK_PROMPT.format_messages(
                    tagline=asset["tagline"],
                    story=asset["story"],
                    image_prompt=asset["image_prompt"]
                )
            )
            
            checked_assets.append({
                **asset,
                "quality_check": quality_check_response.content
            })

        state["campaign_assets"] = checked_assets
        return state

    def should_continue(self, state: GraphState) -> bool:
        """Determine if the workflow should continue based on quality check."""
        assets = state.get("campaign_assets", [])
        if not assets:
            return False
            
        # Check if any assets failed quality check
        for asset in assets:
            quality_check = asset.get("quality_check", "")
            if "fail" in quality_check.lower() or "error" in quality_check.lower():
                return False
                
        return True
