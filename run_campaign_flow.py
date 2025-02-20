import os
import sys
import asyncio
import argparse
import json

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.claude_llm import create_claude_llm
from src.config.settings import load_settings
from src.core.tools import create_tavily_tool
from src.agents.research.agent import ResearchAgent
from src.agents.marketing.agent import MarketingAgent
from src.agents.AdGen.orchestrator import AdCampaignOrchestrator
from src.agents.AdGen.ad_content_generator import CreativeAgent
from src.agents.AdGen.image_gen import SDXLTurboGenerator
from src.agents.marketing.agent import parse_research_results

async def run_campaign_flow(company_name: str, target_audience: str):
    """
    Run the end-to-end campaign generation flow.
    
    Args:
        company_name: Name of the company to generate campaign for
        target_audience: Description of the target audience
    """
    try:
        # Load settings and API keys
        settings = load_settings()
        
        # Initialize LLM
        llm = create_claude_llm(api_key=settings.claude_api_key)
        tavily_tool = create_tavily_tool(api_key=settings.tavily_api_key)
        tools = [tavily_tool]  # Add your tools here
        
        # Step 1: Research Phase
        print("\n=== Starting Research Phase ===")
        research_agent = ResearchAgent(
            llm=llm,
            tools=tools,
            verbose=True
        )
        await research_agent.initialize()
        
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
        
        parsed_results = parse_research_results(research_results)
        
        marketing_results = await marketing_agent.run(
            company_summary=parsed_results["company_summary"],
            target_audience=target_audience,
            brand_values=parsed_results["analysis"]
        )
        print(f"\nMarketing Campaign Ideas:\n{marketing_results}")
        
        # Step 3: Ad Generation Phase
        print("\n=== Starting Ad Generation Phase ===")
        creative_agent = CreativeAgent(
            llm=llm,
            tools=tools,
            verbose=True
        )
        await creative_agent.initialize()
        
        image_generator = SDXLTurboGenerator()
        
        orchestrator = AdCampaignOrchestrator(
            creative_agent=creative_agent,
            image_generator=image_generator,
            llm=llm
        )
        
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
        
        campaign_results = await orchestrator.generate_campaign(
            brand_info=parsed_results["company_summary"],
            target_audience=target_audience,
            campaign_goals="Increase brand awareness and drive product adoption",
            campaign_ideas=campaign_ideas
        )
        
        return {
            "research_results": research_results,
            "marketing_results": marketing_results,
            "campaign_results": campaign_results
        }
        
    except Exception as e:
        print(f"\nError running campaign flow: {str(e)}")
        raise

async def main_async(company_name: str, target_audience: str, output_file: str = None):
    """Run the campaign flow and optionally save results."""
    results = await run_campaign_flow(company_name, target_audience)
    
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {output_file}")
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Run end-to-end campaign generation flow')
    parser.add_argument('company_name', help='Name of the company')
    parser.add_argument('target_audience', help='Description of target audience')
    parser.add_argument('--output', '-o', help='Output file to save results (optional)')
    
    args = parser.parse_args()
    
    asyncio.run(main_async(
        company_name=args.company_name,
        target_audience=args.target_audience,
        output_file=args.output
    ))

if __name__ == "__main__":
    main()
