import os
import asyncio
from typing import Dict, List
import pytest
from langchain.tools import Tool
from src.core.claude_llm import create_claude_llm
from src.agents.research.agent import ResearchAgent
from src.agents.marketing.agent import MarketingAgent
from src.agents.AdGen.orchestrator import AdCampaignOrchestrator
from src.agents.AdGen.ad_content_generator import CreativeAgent
from src.agents.AdGen.image_gen import SDXLTurboGenerator

@pytest.mark.asyncio
async def test_end_to_end_campaign_generation():
    """Test the complete flow from research to final ad campaign generation."""
    
    # Initialize LLM
    llm = create_claude_llm()
    
    # Initialize tools (add your actual tools here)
    tools: List[Tool] = []
    
    # Step 1: Research Phase
    print("\n=== Starting Research Phase ===")
    research_agent = ResearchAgent(
        llm=llm,
        tools=tools,
        verbose=True
    )
    await research_agent.initialize()
    
    # Example company and target audience
    company_name = "EcoTech Solutions"
    target_audience = "Environmentally conscious urban professionals, 25-45 years old"
    
    # Run research
    research_results = await research_agent.run(
        company_name=company_name,
        target_audience=target_audience
    )
    print(f"\nResearch Results:\n{research_results}")
    
    # Step 2: Marketing Strategy Phase
    print("\n=== Starting Marketing Strategy Phase ===")
    marketing_agent = MarketingAgent(
        llm=llm,
        tools=tools,
        verbose=True
    )
    await marketing_agent.initialize()
    
    # Parse research results
    parsed_results = marketing_agent.parse_research_results(research_results)
    
    # Generate marketing campaign ideas
    marketing_results = await marketing_agent.run(
        company_summary=parsed_results["company_summary"],
        target_audience=target_audience,
        brand_values=parsed_results["analysis"]
    )
    print(f"\nMarketing Campaign Ideas:\n{marketing_results}")
    
    # Step 3: Ad Generation Phase
    print("\n=== Starting Ad Generation Phase ===")
    
    # Initialize required components
    creative_agent = CreativeAgent(
        llm=llm,
        tools=tools,
        verbose=True
    )
    await creative_agent.initialize()
    
    image_generator = SDXLTurboGenerator()
    
    # Initialize orchestrator
    orchestrator = AdCampaignOrchestrator(
        creative_agent=creative_agent,
        image_generator=image_generator,
        llm=llm
    )
    
    # Prepare campaign ideas
    campaign_ideas = [
        {
            "campaign_name": "EcoTech Innovation Campaign",
            "core_message": "Sustainable technology for a better tomorrow",
            "visual_theme_description": "Modern, clean design with nature elements",
            "key_emotional_appeal": "Hope and empowerment",
            "prompt_suggestions": {
                "product_focused": "Sleek eco-friendly technology products",
                "brand_focused": "Innovation meets sustainability",
                "social_media": "Instagram-optimized lifestyle imagery"
            },
            "brand_info": parsed_results["company_summary"],
            "target_audience": target_audience,
            "campaign_goals": "Increase brand awareness and drive product adoption"
        }
    ]
    
    # Generate ad campaign
    campaign_results = await orchestrator.generate_campaign(
        brand_info=parsed_results["company_summary"],
        target_audience=target_audience,
        campaign_goals="Increase brand awareness and drive product adoption",
        campaign_ideas=campaign_ideas
    )
    
    # Verify results
    assert len(campaign_results) > 0, "No campaigns were generated"
    
    first_campaign = campaign_results[0]
    assert "campaign_name" in first_campaign, "Campaign name missing"
    assert "campaign_dir" in first_campaign, "Campaign directory missing"
    assert "assets" in first_campaign, "Campaign assets missing"
    
    # Verify asset files exist
    assets = first_campaign["assets"]
    assert os.path.exists(assets["tagline"]), "Tagline file not found"
    assert os.path.exists(assets["story"]), "Story file not found"
    assert os.path.exists(assets["image"]), "Image file not found"
    assert os.path.exists(assets["details"]), "Details file not found"
    
    print("\n=== End-to-End Flow Completed Successfully ===")
    print(f"Campaign outputs saved to: {first_campaign['campaign_dir']}")
    
    return {
        "research_results": research_results,
        "marketing_results": marketing_results,
        "campaign_results": campaign_results
    }

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_end_to_end_campaign_generation())
