import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print(sys.path)

from src.agents.marketing.agent import MarketingAgent, parse_research_results
from src.agents.research.agent import ResearchAgent
from src.core.claude_llm import create_claude_llm
from src.core.llm import create_azure_llm
from src.config.settings import load_settings
from src.core.tools import create_tavily_tool

import asyncio

async def test_marketing_agent():
    # Load settings and API keys
    settings = load_settings()

    # Initialize LLM
    # llm = create_azure_llm(azure_settings=settings.azure)
    claude_llm = create_claude_llm(
        api_key=settings.claude_api_key,
        model_name="claude-3-haiku-20240307",
        temperature=0.7
    )

    # Create Tavily search tool
    tavily_tool = create_tavily_tool(api_key=settings.tavily_api_key)

    # Initialize Research Agent
    research_agent = ResearchAgent(
        llm=claude_llm,
        tools=[tavily_tool],
        model_name="claude-3-haiku-20240307",
        temperature=0.7,
        verbose=True
    )
    await research_agent.initialize()

    # Initialize Marketing Agent
    marketing_agent = MarketingAgent(llm=claude_llm, 
                                     tools=[tavily_tool])
    await marketing_agent.initialize()

    # Get input from the user
    company_name = 'Audi' # input("Enter the company name to research: ")
    target_audience = 'Men Aged between 20 and 40' # input("Enter the target audience: ")

    # Run the research agent
    research_results = await research_agent.run(company_name, target_audience)
    
    print(f"Research Results: {research_results}")

    # Parse research results
    parsed_results = parse_research_results(research_results)
    company_summary = parsed_results["company_summary"]
    analysis = parsed_results["analysis"]
    brand_values = analysis[:200]  # Limit to 200 characters

    # Run the marketing agent
    campaign_ideas = await marketing_agent.run(company_summary, target_audience, brand_values)

    # Print the results
    print("Campaign Ideas:")
    print(campaign_ideas)

if __name__ == "__main__":
    asyncio.run(test_marketing_agent())
