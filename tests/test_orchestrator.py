import os
from src.agents.AdGen.orchestrator import AdCampaignOrchestrator
from src.agents.AdGen.ad_content_generator import CreativeAgent
from campaign_generator import CampaignIdeaGenerator
from src.agents.AdGen.image_gen import SDXLTurboGenerator
from src.core.llm import create_azure_llm
from src.config.settings import load_settings
from src.core.tools import create_tavily_tool

def test_orchestrator():
    # Load settings and API keys
    settings = load_settings()

    # Initialize LLM
    llm = create_azure_llm(azure_settings=settings.azure)

    # Create Tavily search tool
    tavily_tool = create_tavily_tool(api_key=settings.tavily_api_key)

    # Initialize agents
    creative_agent = CreativeAgent(llm=llm, tools=[tavily_tool])
    creative_agent.initialize()
    campaign_generator = CampaignIdeaGenerator(llm=llm)
    image_generator = SDXLTurboGenerator()

    # Initialize Orchestrator
    orchestrator = AdCampaignOrchestrator(creative_agent=creative_agent, campaign_generator=campaign_generator, image_generator=image_generator)

    # Get input from the user
    company_summary = input("Enter the company summary: ")
    target_audience = input("Enter the target audience: ")
    brand_values = input("Enter the brand values: ")

    company_analysis = {
        "company_summary": company_summary,
        "target_audience": target_audience,
        "brand_values": brand_values
    }

    # Generate campaign ideas
    campaign_ideas = campaign_generator.generate_campaign_ideas(company_analysis)

    # Run the orchestrator
    assets = orchestrator.generate_campaign_assets(campaign_ideas)

    # Print the results
    print("Generated Assets:")
    print(assets)

if __name__ == "__main__":
    test_orchestrator()
