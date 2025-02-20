from typing import TypedDict, Dict, List, Any

class CampaignIdeas(TypedDict):
    campaign_name: str
    core_message: str
    visual_theme_description: str
    key_emotional_appeal: str
    prompt_suggestions: Dict[str, str]

class StrategyAnalysis(TypedDict):
    brand_info: str
    target_audience: str
    campaign_goals: str

class CreativeDirection(TypedDict):
    tagline: str
    story: str
    image_prompt: str

class CampaignAssets(TypedDict):
    tagline_path: str
    story_path: str
    image_path: str
    details_path: str

class GraphState(TypedDict):
    strategy_analysis: StrategyAnalysis
    creative_direction: CreativeDirection
    campaign_assets: CampaignAssets
    campaign_ideas: List[CampaignIdeas]
