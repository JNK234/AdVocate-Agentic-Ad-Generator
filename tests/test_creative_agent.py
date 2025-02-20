import os
from src.agents.AdGen.ad_content_generator import CreativeAgent
from src.core.llm import create_azure_llm
from src.config.settings import load_settings
from src.core.tools import create_tavily_tool

def test_creative_agent():
    # Load settings and API keys
    settings = load_settings()

    # Initialize LLM
    llm = create_azure_llm(azure_settings=settings.azure)

    # Create Tavily search tool
    tavily_tool = create_tavily_tool(api_key=settings.tavily_api_key)

    # Initialize Creative Agent
    creative_agent = CreativeAgent(llm=llm, tools=[tavily_tool])
    creative_agent.initialize()

    # Get input from the user
    campaign_name = input("Enter the campaign name: ")
    core_message = input("Enter the core message: ")
    visual_theme_description = input("Enter the visual theme description: ")

    campaign_data = {
        "campaign_name": campaign_name,
        "core_message": core_message,
        "visual_theme_description": visual_theme_description
    }

    # Run the agent
    assets = creative_agent.generate_campaign_assets(campaign_data)

    # Print the results
    print("Generated Assets:")
    print(assets)

if __name__ == "__main__":
    test_creative_agent()
