from typing import Dict, Optional, TypedDict
from langchain.tools import Tool
from .prompts import CAMPAIGN_GENERATION_PROMPT
from .types import GraphState

class MarketingNodes:
    def __init__(self, llm, agent):
        self.llm = llm
        self.agent = agent

    async def analyze_company(self, state: GraphState) -> Dict:
        company_summary = state['company_summary']
        target_audience = state['target_audience']
        brand_values = state['brand_values']
        
        
        print(f'Analyzing company: {company_summary}')
        
        # This node might perform some analysis or formatting of the input data
        # For now, it simply passes the data through
        return {
            "company_summary": company_summary,
            "target_audience": target_audience,
            "brand_values": brand_values
        }
        
    async def generate_campaigns(self, state: GraphState) -> Dict:
        company_summary = state['company_summary']
        target_audience = state['target_audience']
        brand_values = state['brand_values']
        
        print("Generating Campaigns.....")
        
        response = await self.llm.ainvoke(
            CAMPAIGN_GENERATION_PROMPT.format_messages(
                company_summary=company_summary,
                target_audience=target_audience,
                brand_values=brand_values
            )
        )
        
        # Parse the response to extract the campaign ideas from the Action Input
        content = response.content
        try:
            # Split by sections
            sections = content.split("Action Input:")
            if len(sections) < 2:
                raise ValueError("Response missing Action Input section")
            
            campaign_ideas = sections[1].strip()
            return {"campaign_ideas": campaign_ideas}
        except Exception as e:
            print(f"Error parsing LLM response: {str(e)}")
            return {"campaign_ideas": content}  # Fallback to full content if parsing fails
