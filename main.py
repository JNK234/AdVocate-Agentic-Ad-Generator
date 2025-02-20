"""
Main entry point for the research agent application.
"""
import asyncio
from src.config.settings import load_settings
from src.core.llm import create_llm
from src.core.tools import create_tavily_tool
from src.agents.research.agent import ResearchAgent

async def main():
    """
    Main function to run the research agent.
    """
    try:
        # Load settings
        settings = load_settings()
        
        # Initialize LLM
        llm = create_llm(settings.azure)
        
        # Create tools
        tavily_tool = create_tavily_tool(settings.tavily_api_key)
        tools = [tavily_tool]
        
        # Initialize research agent
        agent = ResearchAgent(llm=llm, tools=tools)
        agent.initialize()
        
        print("Research Agent initialized successfully!")
        print("Type 'exit' to quit the application.\n")
        
        while True:
            # Get company name from user
            company_name = input("\nEnter company name to research: ").strip()
            
            if company_name.lower() == 'exit':
                print("\nGoodbye!")
                break
            
            print(f"\nResearching {company_name}...")
            
            # Run research
            results = await agent.run(company_name)
            
            print("\nResearch Results:")
            print("=" * 80)
            print(results)
            print("=" * 80)
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
