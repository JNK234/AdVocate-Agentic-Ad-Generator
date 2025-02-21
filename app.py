import os
import sys
import asyncio
import streamlit as st
from datetime import datetime
import plotly.graph_objects as go
from pathlib import Path
import json
import re
from dataclasses import dataclass
from typing import List, Optional

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.research.agent import ResearchAgent
from src.agents.marketing.agent import MarketingAgent, parse_research_results
from src.agents.AdGen.orchestrator import AdCampaignOrchestrator
from src.agents.AdGen.ad_content_generator import CreativeAgent
from src.core.claude_llm import create_claude_llm
from src.config.settings import load_settings
from src.core.tools import create_tavily_tool
from langchain.agents import AgentType
from src.agents.AdGen.image_gen import SDXLTurboGenerator

@dataclass
class Campaign:
    # Display fields
    name: str
    core_message: str
    visual_theme: str
    emotional_appeal: str
    timeline: str
    success_metrics: List[str]
    
    # Additional fields for asset generation
    social_media_focus: str = ""
    photography_style: str = ""
    color_palette: str = ""
    key_visual_elements: str = ""
    mood_atmosphere: str = ""
    budget_allocation: str = ""
    engagement_tactics: str = ""
    hashtag_strategy: str = ""
    risk_mitigation: str = ""

def parse_campaign_details(marketing_results: str) -> List[Campaign]:
    """Parse campaign details from marketing results string"""
    campaigns = []
    
    print(marketing_results)
    
    # Split into individual campaigns
    campaign_sections = re.split(r'Campaign Idea \d+:', marketing_results)
    campaign_sections = [s.strip() for s in campaign_sections if s.strip()]
    
    for section in campaign_sections:
        try:
            # Extract all fields using regex
            name_match = re.search(r'(?:1\.|Campaign Name:?)\s*["""]?(.*?)["""]?\s*(?=2\.|Core Message|$)', section, re.DOTALL)
            message_match = re.search(r'(?:2\.|Core Message:?)\s*(.*?)(?=3\.|Visual Theme|$)', section, re.DOTALL)
            theme_match = re.search(r'(?:3\.|Visual Theme Description:?)\s*(.*?)(?=4\.|Key Emotional Appeal|$)', section, re.DOTALL)
            appeal_match = re.search(r'(?:4\.|Key Emotional Appeal:?)\s*(.*?)(?=5\.|Social Media Focus|$)', section, re.DOTALL)
            timeline_match = re.search(r'(?:6\.|Campaign Timeline:?)\s*(.*?)(?=7\.|Success Metrics|$)', section, re.DOTALL)
            metrics_match = re.search(r'(?:7\.|Success Metrics:?)\s*(.*?)(?=8\.|Budget Allocation|$)', section, re.DOTALL)
            
            # Extract detailed visual theme components
            theme_text = theme_match.group(1) if theme_match else ""
            color_palette = re.search(r'Color Palette:?\s*(.*?)(?=Photography Style|$)', theme_text, re.DOTALL)
            photography = re.search(r'Photography Style:?\s*(.*?)(?=Key Visual Elements|$)', theme_text, re.DOTALL)
            visual_elements = re.search(r'Key Visual Elements:?\s*(.*?)(?=Mood and Atmosphere|$)', theme_text, re.DOTALL)
            mood = re.search(r'Mood and Atmosphere:?\s*(.*?)(?=$)', theme_text, re.DOTALL)
            
            # Extract social media and budget details
            social_match = re.search(r'Social Media Focus:?\s*(.*?)(?=Campaign Timeline|$)', section, re.DOTALL)
            budget_match = re.search(r'Budget Allocation:?\s*(.*?)(?=Risk Mitigation|$)', section, re.DOTALL)
            risk_match = re.search(r'Risk Mitigation:?\s*(.*?)(?=$)', section, re.DOTALL)
            
            # Extract engagement and hashtag strategy from social media section
            social_text = social_match.group(1) if social_match else ""
            engagement = re.search(r'Engagement Tactics:?\s*(.*?)(?=Hashtag Strategy|$)', social_text, re.DOTALL)
            hashtags = re.search(r'Hashtag Strategy:?\s*(.*?)(?=$)', social_text, re.DOTALL)
            
            # Extract and clean metrics
            metrics = []
            if metrics_match:
                metrics_text = metrics_match.group(1).strip()
                metrics = [m.strip() for m in metrics_text.split(',')]
            
            # Create campaign with all extracted information
            campaign = Campaign(
                name=name_match.group(1).strip() if name_match else "Untitled Campaign",
                core_message=message_match.group(1).strip() if message_match else "",
                visual_theme=theme_match.group(1).strip() if theme_match else "",
                emotional_appeal=appeal_match.group(1).strip() if appeal_match else "",
                timeline=timeline_match.group(1).strip() if timeline_match else "",
                success_metrics=metrics,
                social_media_focus=social_match.group(1).strip() if social_match else "",
                photography_style=photography.group(1).strip() if photography else "",
                color_palette=color_palette.group(1).strip() if color_palette else "",
                key_visual_elements=visual_elements.group(1).strip() if visual_elements else "",
                mood_atmosphere=mood.group(1).strip() if mood else "",
                budget_allocation=budget_match.group(1).strip() if budget_match else "",
                engagement_tactics=engagement.group(1).strip() if engagement else "",
                hashtag_strategy=hashtags.group(1).strip() if hashtags else "",
                risk_mitigation=risk_match.group(1).strip() if risk_match else ""
            )
            campaigns.append(campaign)
            
        except Exception as e:
            print(f"Error parsing campaign section: {str(e)}")
            continue
    
    return campaigns

# Page configuration
st.set_page_config(
    page_title="AdVocate",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize theme in session state
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'

# Custom CSS with theme support
st.markdown(f"""
    <style>
    /* Base styles */
    .main {{ padding: 2rem; }}
    
    /* Theme-specific styles */
    .theme-light {{
        --bg-color: #ffffff;
        --text-color: #1E1E1E;
        --card-bg: #f8f9fa;
        --card-border: #dee2e6;
        --primary-color: #FF4B4B;
    }}
    
    .theme-dark {{
        --bg-color: #1E1E1E;
        --text-color: #F8F9FA;
        --card-bg: #2D2D2D;
        --card-border: #404040;
        --primary-color: #FF6B6B;
    }}
    
    /* Apply theme */
    .main {{
        background-color: var(--bg-color);
        color: var(--text-color);
    }}
    
    .stButton>button {{
        width: 100%;
        border-radius: 20px;
        height: 3em;
        background-color: var(--primary-color);
        color: white;
        transition: all 0.3s ease;
    }}
    
    .stButton>button:hover {{
        opacity: 0.9;
        transform: translateY(-2px);
    }}
    
    .campaign-card {{
        background-color: var(--card-bg);
        color: var(--text-color);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border: 1px solid var(--card-border);
        transition: transform 0.2s ease;
    }}
    
    .campaign-card:hover {{
        transform: translateY(-2px);
    }}
    
    /* Typography improvements */
    h1, h2, h3 {{
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
        font-weight: 600;
        color: var(--text-color);
    }}
    
    p {{
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        line-height: 1.6;
        color: var(--text-color);
    }}
    </style>
    
    <script>
        document.body.classList.add('theme-{st.session_state.theme}');
    </script>
""", unsafe_allow_html=True)

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
    st.session_state.research_cache = {}
    st.session_state.marketing_cache = {}
    st.session_state.research_history = []
    st.session_state.current_company = ""
    st.session_state.current_audience = ""
    st.session_state.ad_assets = {}
    st.session_state.session_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    st.session_state.progress = 0
    st.session_state.current_step = "start"

async def initialize_agents():
    """Initialize all required agents and tools"""
    if not st.session_state.initialized:
        with st.spinner("Initializing AI agents..."):
            settings = load_settings()
            llm = create_claude_llm(api_key=settings.claude_api_key)
            search_tool = create_tavily_tool(api_key=settings.tavily_api_key)
            tools = [search_tool]
            image_generator = SDXLTurboGenerator()
            
            st.session_state.research_agent = ResearchAgent(llm=llm, tools=tools, verbose=True)
            await st.session_state.research_agent.initialize()
            
            st.session_state.marketing_agent = MarketingAgent(llm=llm, tools=tools, verbose=True)
            await st.session_state.marketing_agent.initialize()
            
            st.session_state.creative_agent = CreativeAgent(llm=llm, tools=tools, verbose=True)
            st.session_state.ad_orchestrator = AdCampaignOrchestrator(
                creative_agent=st.session_state.creative_agent,
                image_generator=image_generator,
                llm=llm
            )
            
            st.session_state.initialized = True
            print("Agents initialized successfully")

def display_landing():
    """Display the landing page"""
    st.title("🎯 AdVocate")
    st.markdown("""
    <div style='text-align: center; margin-bottom: 2rem;'>
        <h3 style='font-style: italic; color: var(--text-color); opacity: 0.9;'>
            AI-Powered Marketing Campaigns That Speak Your Brand's Truth
        </h3>
    </div>
    <div style='padding: 1.5rem; background-color: var(--card-bg); border-radius: 10px; border: 1px solid var(--card-border);'>
        <p style='font-size: 1.1em; margin-bottom: 0;'>
            Transform your marketing vision into compelling campaigns. Enter your company details below to harness the power of AI for your brand.
        </p>
    </div>
    """, unsafe_allow_html=True)

def display_progress():
    """Display progress bar and current step"""
    steps = {"start": 0, "research": 33, "marketing": 66, "campaign": 100}
    progress = steps.get(st.session_state.current_step, 0)
    st.progress(progress/100)

async def get_research_data(company: str, audience: str, force_new: bool = False):
    """Get research data with caching"""
    cache_key = f"{company}_{audience}"
    if not force_new and cache_key in st.session_state.research_cache:
        return st.session_state.research_cache[cache_key]
    
    if not st.session_state.initialized:
        await initialize_agents()
    
    research_data = await st.session_state.research_agent.run(
        company_name=company,
        target_audience=audience
    )
    
    result = {
        "result": research_data,
        "timestamp": datetime.utcnow().isoformat(),
        "source": "new_research"
    }
    
    st.session_state.research_cache[cache_key] = result
    return result

async def get_marketing_data(research_result: str, company: str, audience: str, force_new: bool = False):
    """Get marketing analysis with caching"""
    cache_key = f"marketing_{company}"
    if not force_new and cache_key in st.session_state.marketing_cache:
        return st.session_state.marketing_cache[cache_key]
    
    if not st.session_state.initialized:
        await initialize_agents()
    
    parsed_results = parse_research_results(research_result)
    marketing_data = await st.session_state.marketing_agent.run(
        company_summary=parsed_results["company_summary"],
        target_audience=audience,
        brand_values=parsed_results["analysis"]
    )
    
    result = {
        "result": marketing_data,
        "timestamp": datetime.utcnow().isoformat(),
        "source": "new_analysis"
    }
    
    st.session_state.marketing_cache[cache_key] = result
    return result

async def display_research_phase():
    """Display the research phase interface"""
    st.subheader("🔍 Research Phase")
    
    col1, col2 = st.columns(2)
    with col1:
        company = st.text_input("Company Name")
    with col2:
        audience = st.text_input("Target Audience")
    
    if st.button("Start Research", key="research_button"):
        if company and audience:
            st.session_state.current_company = company
            st.session_state.current_audience = audience
            st.session_state.current_step = "research"
            
            with st.spinner("Conducting market research..."):
                research_data = await get_research_data(company, audience)
                st.session_state.research_history.append({
                    "type": "research",
                    "company": company,
                    "audience": audience,
                    "result": research_data["result"],
                    "timestamp": research_data["timestamp"]
                })
                st.session_state.current_step = "marketing"
                st.rerun()
        else:
            st.error("Please enter both company name and target audience")

async def display_marketing_phase():
    """Display the marketing analysis phase"""
    if st.session_state.research_history:
        latest_research = st.session_state.research_history[-1]
        with st.spinner("Generating marketing analysis..."):
            marketing_data = await get_marketing_data(
                latest_research["result"],
                latest_research["company"],
                st.session_state.current_audience
            )
            st.session_state.current_step = "campaign"
            st.rerun()
    else:
        st.info("Please complete the research phase first")

async def display_campaign_generation():
    """Display campaign generation interface with simplified UI"""
    st.subheader("💡 Generated Campaigns")
    
    if st.session_state.current_step == "campaign":
        try:
            marketing_data = st.session_state.marketing_cache.get(
                f"marketing_{st.session_state.current_company}", {}
            ).get("result", "")
            
            campaigns = parse_campaign_details(marketing_data)
            
            if campaigns:
                for i, campaign in enumerate(campaigns):
                    with st.container():
                        st.markdown(f"""
                        <div class="campaign-card">
                            <h3 style="font-size: 1.8em; margin-bottom: 1rem;">{campaign.name}</h3>
                            <div style="display: grid; gap: 1rem;">
                                <div style="background: rgba(255, 75, 75, 0.1); padding: 1rem; border-radius: 8px;">
                                    <h4 style="margin: 0; color: var(--primary-color);">Core Message</h4>
                                    <p style="margin: 0.5rem 0 0 0;">{campaign.core_message}</p>
                                </div>
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                                    <div>
                                        <h4 style="color: var(--text-color);">Visual Theme</h4>
                                        <p>{campaign.visual_theme}</p>
                                    </div>
                                    <div>
                                        <h4 style="color: var(--text-color);">Emotional Appeal</h4>
                                        <p>{campaign.emotional_appeal}</p>
                                    </div>
                                </div>
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                                    <div>
                                        <h4 style="color: var(--text-color);">Timeline</h4>
                                        <p>{campaign.timeline}</p>
                                    </div>
                                    <div>
                                        <h4 style="color: var(--text-color);">Success Metrics</h4>
                                        <ul style="margin: 0.5rem 0 0 1.2rem; padding: 0;">
                            {' '.join([f'<li>{metric}</li>' for metric in campaign.success_metrics])}
                                        </ul>
                                    </div>
                                </div>
                                <p style="color: var(--text-color); opacity: 0.8; font-size: 0.9em; margin-top: 0.5rem; text-align: center;">
                                    <i>✨ Additional details available for asset generation including color palette, photography style, and social media strategy.</i>
                                </p>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button(f"Generate Assets for Campaign {i+1}", key=f"gen_assets_{i}"):
                            with st.spinner("Generating campaign assets..."):
                                try:
                                    # Pass complete campaign information to asset generation
                                    campaign_dict = {
                                        "campaign_name": campaign.name,
                                        "core_message": campaign.core_message,
                                        "visual_theme_description": campaign.visual_theme,
                                        "key_emotional_appeal": campaign.emotional_appeal,
                                        "success_metrics": campaign.success_metrics,
                                        "prompt_suggestions": {
                                            "brand_focused": campaign.core_message,
                                            "visual_focused": f"Color Palette: {campaign.color_palette}\nPhotography Style: {campaign.photography_style}\nKey Elements: {campaign.key_visual_elements}\nMood: {campaign.mood_atmosphere}",
                                            "social_media": f"Focus: {campaign.social_media_focus}\nTactics: {campaign.engagement_tactics}\nHashtags: {campaign.hashtag_strategy}"
                                        }
                                    }
                                    
                                    assets = await st.session_state.ad_orchestrator.generate_single_campaign(campaign_dict)
                                    st.session_state.ad_assets[f"campaign_{i}"] = assets
                                    
                                    st.markdown("""
                                    <div style='background-color: #ffffff; padding: 1.5rem; border-radius: 10px; border: 1px solid #e0e0e0; margin-top: 1rem;'>
                                        <h4>Generated Campaign Assets</h4>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        if os.path.exists(assets['assets']['image']):
                                            st.image(assets['assets']['image'], caption="Campaign Visual", use_container_width=True)
                                        else:
                                            st.warning("Campaign image could not be generated")
                                    
                                    with col2:
                                        try:
                                            with open(assets['assets']['tagline'], 'r') as f:
                                                tagline = f.read().strip()
                                                st.markdown("#### Campaign Tagline")
                                                st.markdown(f"*{tagline}*")
                                        except Exception as e:
                                            st.error("Could not load campaign tagline")
                                        
                                        try:
                                            with open(assets['assets']['story'], 'r') as f:
                                                story = f.read().strip()
                                                st.markdown("#### Campaign Story")
                                                st.markdown(story)
                                        except Exception as e:
                                            st.error("Could not load campaign story")
                                    
                                    # Create zip file with assets
                                    st.markdown("---")
                                    try:
                                        import zipfile
                                        import io
                                        import shutil
                                        
                                        # Create a BytesIO object to store the zip file
                                        zip_buffer = io.BytesIO()
                                        
                                        # Create the zip file
                                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                                            # Add image
                                            if os.path.exists(assets['assets']['image']):
                                                image_ext = os.path.splitext(assets['assets']['image'])[1]
                                                zip_file.write(
                                                    assets['assets']['image'], 
                                                    f'campaign_{i+1}_image{image_ext}'
                                                )
                                            
                                            # Add tagline
                                            with open(assets['assets']['tagline'], 'r') as f:
                                                zip_file.writestr(f'campaign_{i+1}_tagline.txt', f.read())
                                            
                                            # Add story
                                            with open(assets['assets']['story'], 'r') as f:
                                                zip_file.writestr(f'campaign_{i+1}_story.txt', f.read())
                                        
                                        # Reset buffer position
                                        zip_buffer.seek(0)
                                        
                                        # Create download button
                                        col1, col2, col3 = st.columns([1,2,1])
                                        with col2:
                                            st.download_button(
                                                "📥 Download Campaign Assets",
                                                data=zip_buffer,
                                                file_name=f"campaign_{i+1}_assets.zip",
                                                mime="application/zip",
                                                help="Download all campaign assets (image, tagline, and story)"
                                            )
                                            
                                    except Exception as e:
                                        st.error(f"Could not prepare assets for download: {str(e)}")
                                        
                                except Exception as e:
                                    st.error(f"Error generating campaign assets: {str(e)}")
            else:
                st.warning("No valid campaigns were generated. Please try again.")
                
        except Exception as e:
            st.error(f"Error: {str(e)}")

async def main():
    """Main application flow"""
    await initialize_agents()
    
    # Sidebar
    with st.sidebar:
        st.markdown("### Settings")
        theme = st.selectbox(
            "Theme",
            options=['light', 'dark'],
            index=0 if st.session_state.theme == 'light' else 1,
            key='theme_selector'
        )
        if theme != st.session_state.theme:
            st.session_state.theme = theme
            st.rerun()
            
        st.markdown("---")
        st.markdown("### Progress")
        display_progress()
    
    # Main content
    if st.session_state.current_step == "start":
        display_landing()
        await display_research_phase()
    elif st.session_state.current_step == "research":
        await display_research_phase()
    elif st.session_state.current_step == "marketing":
        await display_marketing_phase()
    elif st.session_state.current_step in ["campaign", "assets"]:
        await display_campaign_generation()

if __name__ == "__main__":
    asyncio.run(main())
