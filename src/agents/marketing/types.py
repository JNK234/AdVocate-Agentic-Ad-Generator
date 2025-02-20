from typing import TypedDict, Optional

class GraphState(TypedDict):
    company_summary: str
    target_audience: str
    brand_values: str
    campaign_ideas: Optional[str]
