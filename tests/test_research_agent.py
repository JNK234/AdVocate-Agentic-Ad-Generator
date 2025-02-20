import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print(sys.path)

from src.agents.research.agent import ResearchAgent
from src.core.claude_llm import create_claude_llm
from src.config.settings import load_settings
from src.core.tools import create_tavily_tool



async def test_research_agent():
    # Load settings and API keys
    settings = load_settings()

    # Create Tavily search tool
    tavily_tool = create_tavily_tool(api_key=settings.tavily_api_key)

    # Initialize Research Agent with Claude
    research_agent = ResearchAgent(
        api_key=settings.claude_api_key,
        tools=[tavily_tool],
        model_name="claude-3-haiku-20240307",
        temperature=0.7,
        verbose=True
    )
    await research_agent.initialize()

    # Get input from the user
    company_name = "Audi" # input("Enter the company name to research: ")
    target_audience = "Men from age 20 to 40" #input("Enter the target audience: ")

    # Run the agent
    research_results = await research_agent.run(company_name, target_audience)

    # Print the results
    print("Research Results:")
    print(research_results)

import asyncio

if __name__ == "__main__":
    asyncio.run(test_research_agent())
