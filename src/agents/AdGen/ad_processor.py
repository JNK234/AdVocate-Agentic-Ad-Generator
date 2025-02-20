import asyncio
import os
import json
from pathlib import Path
from typing import List, Dict
from langchain.chat_models import AzureChatOpenAI
from dotenv import load_dotenv
from .ad_content_generator import CreativeAgent
from .orchestrator import AdCampaignOrchestrator

def process_campaigns(campaigns: List[Dict]) -> List[Dict]:
    """
    Process campaign ideas and generate detailed advertisement content.
    
    Args:
        campaigns: List of campaign dictionaries with ideas and details
        
    Returns:
        List[Dict]: Processed campaigns with generated content
    """
    processed_campaigns = []
    
    for campaign in campaigns:
        # Extract prompt suggestions if they exist
        prompt_suggestions = campaign.get('prompt_suggestions', {})
        
        # Process campaign with different creative angles
        processed_campaign = {
            'campaign_name': campaign['campaign_name'],
            'core_message': campaign.get('core_message', ''),
            'visual_theme': campaign.get('visual_theme_description', {}),
            'emotional_appeal': campaign.get('key_emotional_appeal', {}),
            'social_media_strategy': campaign.get('social_media_focus', {}),
            'generated_content': {
                'product_focused': {
                    'prompt': prompt_suggestions.get('product_focused', ''),
                    'variations': []  # Would be populated by image generation
                },
                'brand_focused': {
                    'prompt': prompt_suggestions.get('brand_focused', ''),
                    'variations': []  # Would be populated by image generation
                },
                'social_media': {
                    'prompt': prompt_suggestions.get('social_media', ''),
                    'variations': []  # Would be populated by image generation
                }
            },
            'campaign_timeline': campaign.get('campaign_timeline', ''),
            'success_metrics': campaign.get('success_metrics', ''),
            'budget_allocation': campaign.get('budget_allocation', '')
        }
        
        processed_campaigns.append(processed_campaign)
    
    return processed_campaigns

def save_processed_campaigns(campaigns: List[Dict], output_path: str) -> None:
    """
    Save processed campaigns to a JSON file.
    
    Args:
        campaigns: List of processed campaign dictionaries
        output_path: Path to save the JSON file
    """
    # Create directory if it doesn't exist
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Save to JSON file
    with open(output_path, 'w') as f:
        json.dump(campaigns, f, indent=2)

async def test_ad_generation():
    # Load environment variables
    load_dotenv()
    
    # Initialize Azure OpenAI
    llm = AzureChatOpenAI(
        deployment_name=os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME'),
        openai_api_version=os.getenv('AZURE_OPENAI_API_VERSION'),
        azure_endpoint=os.getenv('AZURE_OPENAI_API_BASE'),
        api_key=os.getenv('AZURE_OPENAI_API_KEY')
    )
    
    # Initialize Creative Agent
    creative_agent = CreativeAgent(llm=llm, tools=[])
    
    # Initialize Orchestrator
    orchestrator = AdCampaignOrchestrator(creative_agent)
    
    # Test company analysis
    test_analysis = {
        "company_summary": """
        EcoTech Solutions is a sustainable technology company specializing in smart home devices.
        They produce energy-efficient thermostats and power monitoring systems that help homeowners
        reduce their carbon footprint while saving money. Their products feature sleek, modern design
        and integrate with most smart home ecosystems.
        """,
        "target_audience": """
        Environmentally conscious homeowners aged 25-45, tech-savvy professionals who value both
        sustainability and modern design. They are willing to invest in quality products that help
        reduce their environmental impact while maintaining a comfortable lifestyle.
        """,
        "brand_values": """
        Innovation, Sustainability, User-Friendly Design, Environmental Responsibility, Quality
        """
    }
    
    # Generate campaign assets
    results = await orchestrator.generate_campaign_assets(test_analysis)
    
    # Print results
    print("\nGenerated Campaigns:")
    for result in results:
        print(f"\nCampaign: {result['campaign_name']}")
        print(f"Directory: {result['campaign_dir']}")
        print("Assets:")
        for asset_type, path in result['assets'].items():
            print(f"- {asset_type}: {path}")

# if __name__ == "__main__":
#     # Run the test
#     asyncio.run(test_ad_generation())
