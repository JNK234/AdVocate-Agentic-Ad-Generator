from langchain_core.pydantic_v1 import BaseModel

class MyBaseModel(BaseModel):
    class Config:
        arbitrary_types_allowed = True

import streamlit as st
import asyncio, os
from pathlib import Path
from datetime import datetime

from src.agents.research.agent import ResearchAgent
from marketing_strategy_agent import MarketingAgent
from src.agents.AdGen.orchestrator import AdCampaignOrchestrator
from src.agents.AdGen.ad_content_generator import CreativeAgent
from src.core.claude_llm import create_claude_llm
from src.core.tools import create_tavily_tool
from src.config.settings import load_settings, Settings
from src.core.llm import create_azure_llm


tool = create_tavily_tool(api_key='')

# Page configuration
st.set_page_config(
    page_title="AdVocate - You Advertising Assistant",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        margin-top: 1rem;
    }
    .success-message {
        padding: 1rem;
        background-color: #d4edda;
        border-color: #c3e6cb;
        color: #155724;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }
    .campaign-card {
        padding: 1.5rem;
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'settings' not in st.session_state:
    st.session_state.settings = load_settings()
if 'research_results' not in st.session_state:
    st.session_state.research_results = None
if 'campaign_ideas' not in st.session_state:
    st.session_state.campaign_ideas = None
if 'generated_assets' not in st.session_state:
    st.session_state.generated_assets = None
if 'llm' not in st.session_state:
    st.session_state.llm = create_azure_llm(azure_settings=st.session_state.settings.azure)

# Sidebar
with st.sidebar:
    st.title("🎯 Campaign Generator")
    st.markdown("---")
    
    # Input fields
    company_name = st.text_input("Company Name", placeholder="e.g., EcoTech Solutions")
    
    target_audience = st.text_area(
        "Target Audience", 
        placeholder="e.g., Environmentally conscious homeowners aged 30-50..."
    )
    
    st.markdown("### Campaign Settings")
    num_campaigns = st.slider("Number of Campaigns", 1, 5, 3)
    
    include_research = st.checkbox("Include Market Research", value=True)
    generate_visuals = st.checkbox("Generate Visual Assets", value=True)

def run_research_phase(company_name: str):
    """Execute the research phase"""
    with st.spinner("🔍 Conducting market research..."):
        # Initialize research agent
        # llm = create_claude_llm(api_key=st.session_state.settings.claude_api_key)
                
        # Create Tavily search tool from existing tools.py
        tavily_tool = create_tavily_tool(st.session_state.settings.tavily_api_key)
        research_agent = ResearchAgent(
            llm=st.session_state.llm, 
            tools=[tavily_tool],
            verbose=True
        )
        research_agent.initialize()
        
        # Run research
        st.session_state.research_results = asyncio.run(research_agent.run(company_name))
        
        print(f"Got the research results: {st.session_state.research_results}")
        
        return st.session_state.research_results

def run_marketing_phase(research_results: str, target_audience: str):
    """Execute the marketing phase"""
    with st.spinner("📊 Generating marketing strategy..."):
        # Initialize marketing agent
        # llm = create_claude_llm(api_key=st.session_state.settings.claude_api_key)
        tavily_tool = create_tavily_tool(st.session_state.settings.tavily_api_key)
        marketing_agent = MarketingAgent(
            llm=st.session_state.llm, 
            tools=[tavily_tool],
            verbose=True,
            num_campaigns=num_campaigns
        )
        marketing_agent.initialize()
        
        # Create company analysis structure expected by marketing agent
        company_analysis = {
            "company_summary": research_results if research_results else "",
            "target_audience": target_audience,
            "brand_values": "Innovation, Quality, Customer Focus, Market Leadership"
        }
        
        # Generate campaigns
        st.session_state.campaign_ideas = asyncio.run(marketing_agent.run(company_analysis))
        
        print(f"Campaingingngn done....")
        
        return st.session_state.campaign_ideas

def run_asset_generation(campaign_ideas: list):
    """Execute the asset generation phase"""
    with st.spinner("🎨 Generating campaign assets..."):
        try:
            # Initialize creative agent
            # llm = create_claude_llm(api_key=st.session_state.settings.claude_api_key)
            creative_agent = CreativeAgent(llm=st.session_state.llm, tools=[tool])
            creative_agent.initialize()
            
            print(f"Initialized creative agent")

            from .agents.marketing.campaign_generator import CampaignIdeaGenerator
            from .agents.AdGen.image_gen import SDXLTurboGenerator

            campaign_generator = CampaignIdeaGenerator(llm=st.session_state.llm)
            image_generator = SDXLTurboGenerator()
            
            # Initialize orchestrator with creative agent, campaign generator, and image generator
            orchestrator = AdCampaignOrchestrator(creative_agent=creative_agent, campaign_generator=campaign_generator, image_generator=image_generator)
            print(f"Initialized orchestrator, output dir: {orchestrator.output_dir}")
            
            # Ensure Outputs directory exists
            if not os.path.exists("Outputs"):
                os.makedirs("Outputs")
                print("Created Outputs directory")
            
            # Generate campaign assets
            print(f"Generating assets for {len(campaign_ideas)} campaigns")
            st.session_state.generated_assets = asyncio.run(orchestrator.generate_campaign_assets(campaign_ideas))
            print(f"Generated assets: {st.session_state.generated_assets}")
            
            return st.session_state.generated_assets
        except Exception as e:
            print(f"Error in asset generation: {str(e)}")
            raise e

# Main content area
st.title("AdVocate - AI Ad Campaign Generator")
st.markdown("""
Generate comprehensive advertising campaigns powered by AI. 
From market research to final assets, create compelling campaigns that resonate with your audience.
""")

# Start button
if st.button("Generate Campaign", disabled=not (company_name and target_audience)):
    # Research Phase
    if include_research:
        try:
            research_results = run_research_phase(company_name)
            st.markdown("### 📊 Research Results")
            with st.expander("View Research Report", expanded=True):
                st.markdown(research_results)
        except Exception as e:
            st.error(f"Error during research phase: {str(e)}")
            st.stop()
    
    # Marketing Phase
    try:
        campaign_ideas = run_marketing_phase(
            st.session_state.research_results if include_research else "",
            target_audience
        )
        
        print(f"HULALALALAL")
        
        st.markdown("### 💡 Campaign Ideas")
        cols = st.columns(len(campaign_ideas))
        for idx, (campaign, col) in enumerate(zip(campaign_ideas, cols)):
            with col:
                st.markdown(f"#### Campaign {idx + 1}")
                st.markdown(f"**{campaign['campaign_name']}**")
                st.markdown(f"*Core Message:* {campaign['core_message']}")
                
                with st.expander("Campaign Details"):
                    st.markdown(f"**Visual Theme:**\n{campaign['visual_theme_description']}")
                    st.markdown(f"**Emotional Appeal:**\n{campaign.get('key_emotional_appeal', '')}")
                    st.markdown(f"**Social Media Focus:**\n{campaign.get('social_media_focus', '')}")
    except Exception as e:
        st.error(f"Error during marketing phase: {str(e)}")
        st.stop()
    
    # Asset Generation Phase
    if generate_visuals:
        try:
            assets = run_asset_generation(campaign_ideas)
            print("FONOENOENON")
            
            st.markdown("### 🎨 Generated Assets")
            print(assets)
            for asset_set in assets:
                with st.expander(f"Assets for {asset_set['campaign_name']}", expanded=True):
                    # Display assets
                    cols = st.columns(3)
                    
                    try:
                        # Tagline
                        with cols[0]:
                            st.markdown("#### Tagline")
                            with open(asset_set['assets']['tagline'], 'r') as f:
                                st.code(f.read(), language=None)
                        
                        # Story
                        with cols[1]:
                            st.markdown("#### Story")
                            with open(asset_set['assets']['story'], 'r') as f:
                                st.markdown(f.read())
                        
                        # Image
                        with cols[2]:
                            st.markdown("#### Generated Image")
                            if Path(asset_set['assets']['image']).exists():
                                st.image(asset_set['assets']['image'])
                            else:
                                st.warning("Image file not found")
                    except (FileNotFoundError, IOError) as e:
                        st.error(f"Error accessing asset files: {str(e)}")
                        continue
        except Exception as e:
            st.error(f"Error during asset generation: {str(e)}")
            st.stop()
    
    # Success message
    st.markdown("""
        <div class="success-message">
            ✅ Campaign generation completed successfully!
        </div>
    """, unsafe_allow_html=True)

# Display helpful information when no campaign is generated yet
if not st.session_state.campaign_ideas:
    st.info("""
        👋 Welcome to the AI Ad Campaign Generator!
        
        To get started:
        1. Enter your company name
        2. Describe your target audience
        3. Adjust campaign settings in the sidebar
        4. Click "Generate Campaign"
        
        The AI will analyze your inputs and create a comprehensive marketing campaign including research, 
        strategy, and creative assets.
    """)
