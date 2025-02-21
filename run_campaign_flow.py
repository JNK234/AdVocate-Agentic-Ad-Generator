import os
import sys
import asyncio
import argparse
import json
import re
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Custom exceptions
class CampaignFlowError(Exception):
    """Base exception for campaign flow errors"""
    def __init__(self, message: str, step: str, details: Optional[Dict] = None):
        self.message = message
        self.step = step
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(CampaignFlowError):
    """Raised when data validation fails"""
    pass

class ParsingError(CampaignFlowError):
    """Raised when parsing fails"""
    pass

@dataclass
class FlowProgress:
    """Track progress of the campaign flow"""
    step: str
    progress: float
    start_time: datetime
    details: Dict[str, Any]
    
    @property
    def duration(self) -> float:
        return (datetime.utcnow() - self.start_time).total_seconds()

class ProgressTracker:
    """Track progress across multiple steps"""
    def __init__(self):
        self.steps = {}
        self.current_step = None
    
    def start_step(self, step: str, details: Dict[str, Any] = None):
        self.current_step = step
        self.steps[step] = FlowProgress(
            step=step,
            progress=0.0,
            start_time=datetime.utcnow(),
            details=details or {}
        )
    
    def update_progress(self, progress: float, details: Dict[str, Any] = None):
        if self.current_step and self.current_step in self.steps:
            self.steps[self.current_step].progress = progress
            if details:
                self.steps[self.current_step].details.update(details)
    
    def get_current_progress(self) -> Optional[FlowProgress]:
        return self.steps.get(self.current_step)

def validate_research_data(data: Dict) -> bool:
    """Validate research data structure and content"""
    required_fields = ['company_summary', 'market_analysis', 'competitor_analysis']
    
    if not all(field in data for field in required_fields):
        missing = [f for f in required_fields if f not in data]
        raise ValidationError(
            f"Missing required research fields: {', '.join(missing)}",
            'research',
            {'missing_fields': missing}
        )
    
    # Validate content quality
    for field in required_fields:
        if not data[field] or len(data[field].strip()) < 50:
            raise ValidationError(
                f"Insufficient content in {field}",
                'research',
                {'field': field, 'content_length': len(data[field].strip())}
            )
    
    return True

def validate_campaign_data(campaign: Dict) -> bool:
    """Validate campaign data structure and content"""
    required_fields = [
        'campaign_name',
        'core_message',
        'visual_theme_description',
        'key_emotional_appeal'
    ]
    
    if not all(field in campaign for field in required_fields):
        missing = [f for f in required_fields if f not in campaign]
        raise ValidationError(
            f"Missing required campaign fields: {', '.join(missing)}",
            'campaign',
            {'missing_fields': missing}
        )
    
    # Validate content quality
    for field in required_fields:
        if not campaign[field] or len(campaign[field].strip()) < 10:
            raise ValidationError(
                f"Insufficient content in {field}",
                'campaign',
                {'field': field, 'content_length': len(campaign[field].strip())}
            )
    
    return True

from src.core.claude_llm import create_claude_llm
from src.core.openai_llm import create_openai_llm
from src.config.settings import load_settings
from src.core.tools import create_tavily_tool
from src.agents.research.agent import ResearchAgent
from src.agents.marketing.agent import MarketingAgent
from src.agents.AdGen.orchestrator import AdCampaignOrchestrator
from src.agents.AdGen.ad_content_generator import CreativeAgent
from src.agents.AdGen.image_gen import SDXLTurboGenerator
from src.agents.marketing.agent import parse_research_results

def parse_research_results(research_results: str) -> Dict:
    """
    Enhanced parser for research results with validation
    
    Args:
        research_results: Raw research results string
        
    Returns:
        Dictionary containing parsed and validated research data
        
    Raises:
        ParsingError: If parsing fails
        ValidationError: If validation fails
    """
    try:
        # First try to extract sections from the final answer format
        sections = {
            'company_summary': '',
            'market_analysis': '',
            'competitor_analysis': ''
        }
        
        # Look for numbered sections in the research results
        basic_info_match = re.search(r'1\.\s+\*\*Basic Company Information\*\*:(.+?)(?=2\.|$)', research_results, re.DOTALL)
        market_match = re.search(r'3\.\s+\*\*Market Position\*\*:(.+?)(?=4\.|$)', research_results, re.DOTALL)
        audience_match = re.search(r'4\.\s+\*\*Target Audience\*\*:(.+?)(?=$)', research_results, re.DOTALL)
        
        if basic_info_match:
            sections['company_summary'] = basic_info_match.group(1).strip()
        if market_match:
            sections['market_analysis'] = market_match.group(1).strip()
        if audience_match:
            sections['competitor_analysis'] = audience_match.group(1).strip()
            
        # If sections are empty, try alternative format
        if not any(sections.values()):
            # Try to extract from bullet points or dashes
            company_info = re.findall(r'[-•]\s*(.*?)(?=[-•]|$)', research_results, re.DOTALL)
            if company_info:
                sections['company_summary'] = '\n'.join(company_info).strip()
                sections['market_analysis'] = sections['company_summary']  # Use same content as fallback
                sections['competitor_analysis'] = sections['company_summary']  # Use same content as fallback
        
        # If still empty, use the entire research results
        if not any(sections.values()):
            content = research_results.strip()
            if len(content) > 50:  # Minimum content length check
                sections['company_summary'] = content
                sections['market_analysis'] = content
                sections['competitor_analysis'] = content
            else:
                raise ParsingError(
                    "Research results too short or empty",
                    'research',
                    {'content_length': len(content)}
                )
        
        # Validate parsed data
        validate_research_data(sections)
        
        return sections
        
    except (AttributeError, IndexError) as e:
        raise ParsingError(
            "Failed to parse research results",
            'research',
            {'error': str(e), 'research_results': research_results[:100] + '...'}
        )

def parse_campaign_ideas(marketing_results: str) -> List[Dict]:
    """
    Enhanced parser for campaign ideas with validation
    
    Args:
        marketing_results: Raw marketing results string
        
    Returns:
        List of campaign dictionaries with validated fields
        
    Raises:
        ParsingError: If parsing fails
        ValidationError: If validation fails
    """
    if not marketing_results or not marketing_results.strip():
        raise ParsingError(
            "Marketing results are empty",
            'marketing',
            {'marketing_results': marketing_results}
        )
    
    campaigns = []
    
    # Extract success metrics first
    success_metrics = []
    metrics_section = re.search(r'Success Metrics:(.+?)(?=Campaign |$)', marketing_results, re.DOTALL)
    if metrics_section:
        metrics_text = metrics_section.group(1).strip()
        success_metrics = [m.strip() for m in metrics_text.split('\n') if m.strip()]
    
    # Split and parse campaigns
    campaign_sections = re.split(r'### Campaign |## Campaign ', marketing_results)
    campaign_sections = [s for s in campaign_sections if s.strip()]  # Remove empty sections
    
    if not campaign_sections:
        raise ParsingError(
            "No campaign sections found",
            'marketing',
            {'marketing_results': marketing_results[:100] + '...'}
        )
    
    for i, section in enumerate(campaign_sections, 1):
        try:
            # Enhanced regex patterns with better field matching
            patterns = {
                'campaign_name': r'(?:Campaign Name:|Name:)(.+?)(?=Core Message:|$)',
                'core_message': r'Core Message:(.+?)(?=Visual Theme Description:|Visual Theme:|$)',
                'visual_theme': r'Visual Theme(?:\s*Description)?:(.+?)(?=Key Emotional Appeal:|Emotional Appeal:|$)',
                'emotional_appeal': r'(?:Key )?Emotional Appeal:(.+?)(?=Social Media Focus:|Social Media:|$)',
                'social_media': r'Social Media(?:\s*Focus)?:(.+?)(?=Campaign Timeline:|Timeline:|$)',
                'timeline': r'(?:Campaign )?Timeline:(.+?)(?=Budget Allocation:|Budget:|$)',
                'budget': r'Budget(?:\s*Allocation)?:(.+?)(?=Success Metrics:|$)',
            }
            
            # Extract fields with enhanced error handling
            extracted_fields = {}
            for field, pattern in patterns.items():
                match = re.search(pattern, section, re.DOTALL)
                if match:
                    extracted_fields[field] = match.group(1).strip()
            
            # Build campaign dictionary with validation
            campaign = {
                "campaign_name": extracted_fields.get('campaign_name', f'Campaign {i}'),
                "core_message": extracted_fields.get('core_message', ''),
                "visual_theme_description": extracted_fields.get('visual_theme', ''),
                "key_emotional_appeal": extracted_fields.get('emotional_appeal', ''),
                "campaign_timeline": extracted_fields.get('timeline', ''),
                "budget_allocation": extracted_fields.get('budget', ''),
                "success_metrics": success_metrics,
                "prompt_suggestions": {
                    "brand_focused": extracted_fields.get('core_message', ''),
                    "visual_focused": extracted_fields.get('visual_theme', ''),
                    "social_media": extracted_fields.get('social_media', '')
                }
            }
            
            # Validate campaign data
            validate_campaign_data(campaign)
            campaigns.append(campaign)
            
        except ValidationError as ve:
            print(f"Validation error in campaign {i}: {ve.message}")
            continue
        except Exception as e:
            print(f"Error parsing campaign {i}: {str(e)}")
            continue
    
    if not campaigns:
        # Return fallback campaign with validation
        fallback = {
            "campaign_name": "Brand Awareness Campaign",
            "core_message": "Highlighting unique value proposition",
            "visual_theme_description": "Clean, professional design that reflects brand identity",
            "key_emotional_appeal": "Trust and reliability",
            "campaign_timeline": "Q1 2024",
            "budget_allocation": "Standard allocation across channels",
            "success_metrics": ["Increase brand awareness", "Drive engagement"],
            "prompt_suggestions": {
                "brand_focused": "Showcasing brand values and mission",
                "visual_focused": "Professional and trustworthy imagery",
                "social_media": "Engaging content across key platforms"
            }
        }
        validate_campaign_data(fallback)
        campaigns.append(fallback)
    
    return campaigns

async def run_campaign_flow(company_name: str, target_audience: str, progress_tracker: Optional[ProgressTracker] = None):
    """
    Enhanced end-to-end campaign generation flow with progress tracking
    
    Args:
        company_name: Name of the company to generate campaign for
        target_audience: Description of the target audience
        progress_tracker: Optional progress tracker instance
        
    Returns:
        Dictionary containing results from each phase
        
    Raises:
        CampaignFlowError: If any step fails
    """
    # Initialize progress tracking if not provided
    if not progress_tracker:
        progress_tracker = ProgressTracker()
    
    try:
        # Load settings and initialize tools
        settings = load_settings()
        llm = create_openai_llm(api_key=settings.openai_api_key)
        tavily_tool = create_tavily_tool(api_key=settings.tavily_api_key)
        tools = [tavily_tool]
        
        # Step 1: Research Phase
        progress_tracker.start_step('research', {
            'company_name': company_name,
            'target_audience': target_audience
        })
        print("\n=== Starting Research Phase ===")
        
        research_agent = ResearchAgent(llm=llm, tools=tools, verbose=True)
        await research_agent.initialize()
        
        research_results = await research_agent.run(
            company_name=company_name,
            target_audience=target_audience
        )
        
        # Validate research results
        parsed_research = parse_research_results(research_results)
        progress_tracker.update_progress(1.0, {'status': 'completed'})
        
        # Step 2: Marketing Strategy Phase
        progress_tracker.start_step('marketing', {
            'research_summary': parsed_research['company_summary'][:100] + '...'
        })
        print("\n=== Starting Marketing Strategy Phase ===")
        
        marketing_agent = MarketingAgent(llm=llm, tools=tools, verbose=True)
        await marketing_agent.initialize()
            
        marketing_results = await marketing_agent.run(
            company_summary=parsed_research["company_summary"],
            target_audience=target_audience,
            brand_values=parsed_research["market_analysis"]
        )
        
        # Parse and validate campaign ideas
        campaign_ideas = parse_campaign_ideas(marketing_results)
        progress_tracker.update_progress(1.0, {
            'campaigns_generated': len(campaign_ideas)
        })
        
        # Step 3: Ad Generation Phase
        progress_tracker.start_step('ad_generation', {
            'num_campaigns': len(campaign_ideas)
        })
        print("\n=== Starting Ad Generation Phase ===")
        
        creative_agent = CreativeAgent(llm=llm, tools=tools, verbose=True)
        await creative_agent.initialize()
        
        image_generator = SDXLTurboGenerator()
        orchestrator = AdCampaignOrchestrator(
            creative_agent=creative_agent,
            image_generator=image_generator,
            llm=llm
        )
        
        # Update campaigns with research insights
        for campaign in campaign_ideas:
            campaign.update({
                "brand_info": parsed_research["company_summary"],
                "target_audience": target_audience,
                "market_context": parsed_research["market_analysis"],
                "competitor_insights": parsed_research["competitor_analysis"]
            })
        
        # Generate campaign assets
        campaign_results = await orchestrator.generate_campaign(
            brand_info=parsed_research["company_summary"],
            target_audience=target_audience,
            campaign_goals="; ".join(campaign_ideas[0].get("success_metrics", [])),
            campaign_ideas=campaign_ideas
        )
        
        progress_tracker.update_progress(1.0, {
            'assets_generated': len(campaign_results.get('assets', []))
        })
        
        # Compile final results
        results = {
            "research_results": {
                "raw": research_results,
                "parsed": parsed_research
            },
            "marketing_results": {
                "raw": marketing_results,
                "campaigns": campaign_ideas
            },
            "campaign_results": campaign_results,
            "flow_metrics": {
                step: {
                    "duration": prog.duration,
                    "details": prog.details
                } for step, prog in progress_tracker.steps.items()
            }
        }
        
        return results
        
    except CampaignFlowError as e:
        print(f"\nCampaign flow error in {e.step}: {e.message}")
        if e.details:
            print("Error details:", json.dumps(e.details, indent=2))
        raise
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        raise CampaignFlowError(
            f"Unexpected error: {str(e)}",
            progress_tracker.current_step or 'unknown',
            {'error_type': type(e).__name__}
        )

async def main_async(company_name: str, target_audience: str, output_file: str = None):
    """Run the campaign flow with progress tracking and save results."""
    progress_tracker = ProgressTracker()
    results = await run_campaign_flow(
        company_name=company_name,
        target_audience=target_audience,
        progress_tracker=progress_tracker
    )
    
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
