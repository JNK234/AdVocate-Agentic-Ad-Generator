import os
import sys
import asyncio
import streamlit as st
from datetime import datetime
import plotly.graph_objects as go
from pathlib import Path
import json

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

# Page configuration
st.set_page_config(
    page_title="AI Marketing Campaign Generator",
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
        border-radius: 20px;
        height: 3em;
        background-color: #FF4B4B;
        color: white;
    }
    .success-box {
        padding: 1rem;
        border-radius: 10px;
        background-color: #E8F5E9;
        border: 1px solid #4CAF50;
    }
    .info-box {
        padding: 1rem;
        border-radius: 10px;
        background-color: #E3F2FD;
        border: 1px solid #2196F3;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
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
            # Load settings and create LLM
            settings = load_settings()
            llm = create_claude_llm(api_key=settings.claude_api_key)
            
            # Initialize tools
            search_tool = create_tavily_tool(api_key=settings.tavily_api_key)
            tools = [search_tool]
            
            # Image generator
            image_generator = SDXLTurboGenerator()
            
            # Initialize agents
            st.session_state.research_agent = ResearchAgent(
                llm=llm,
                tools=tools,
                verbose=True,
            )
            await st.session_state.research_agent.initialize()
            
            st.session_state.marketing_agent = MarketingAgent(
                llm=llm,
                tools=tools,
                verbose=True,
            )
            await st.session_state.marketing_agent.initialize()
            
            # Initialize creative agent and orchestrator
            st.session_state.creative_agent = CreativeAgent(
                llm=llm,
                tools=tools,
                verbose=True
            )
            st.session_state.ad_orchestrator = AdCampaignOrchestrator(
                creative_agent=st.session_state.creative_agent,
                image_generator=image_generator,
                llm=llm
            )
            
            st.session_state.initialized = True
            
            
            print("Agents initialized successfully")

def display_landing():
    """Display the landing page"""
    st.title("🎯 AI Marketing Campaign Generator")
    
    st.markdown("""
    <div class="info-box">
    Transform your marketing strategy with AI-powered campaign generation. Our system:
    
    * 🔍 Conducts in-depth market research
    * 🎯 Analyzes target audiences
    * 💡 Generates creative campaign ideas
    * 🎨 Creates visual and textual content
    * 📊 Provides performance metrics
    
    Get started by entering your company details below!
    </div>
    """, unsafe_allow_html=True)

def display_progress():
    """Display progress bar and current step"""
    steps = {
        "start": 0,
        "research": 25,
        "marketing": 50,
        "campaign": 75,
        "assets": 100
    }
    
    progress = steps.get(st.session_state.current_step, 0)
    st.progress(progress/100)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("🔍" if progress >= 25 else "⭕")
        st.caption("Research")
    with col2:
        st.markdown("📊" if progress >= 50 else "⭕")
        st.caption("Analysis")
    with col3:
        st.markdown("💡" if progress >= 75 else "⭕")
        st.caption("Campaign")
    with col4:
        st.markdown("🎨" if progress >= 100 else "⭕")
        st.caption("Assets")

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

def create_audience_chart(audience_data):
    """Create a radar chart for audience analysis"""
    categories = ['Age Group', 'Income Level', 'Tech Savvy', 'Brand Loyalty', 'Social Media Usage']
    values = [0.8, 0.6, 0.9, 0.7, 0.85]  # Example values
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Target Audience'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )),
        showlegend=False
    )
    
    return fig

def display_research_phase():
    """Display the research phase interface"""
    st.subheader("🔍 Research Phase")
    
    col1, col2 = st.columns(2)
    
    with col1:
        company = st.text_input(
            "Company Name",
            help="Enter the name of the company you want to analyze"
        )
    
    with col2:
        audience = st.text_input(
            "Target Audience",
            help="Describe your target audience (e.g., 'tech-savvy millennials')"
        )
    
    if st.button("Start Research", key="research_button"):
        if company and audience:
            st.session_state.current_company = company
            st.session_state.current_audience = audience
            st.session_state.current_step = "research"
            
            with st.spinner("Conducting market research..."):
                research_data = asyncio.run(get_research_data(company, audience))
                
                st.session_state.research_history.append({
                    "type": "research",
                    "company": company,
                    "audience": audience,
                    "result": research_data["result"],
                    "source": research_data["source"],
                    "timestamp": research_data["timestamp"]
                })
                
                st.success("Research completed successfully!")
                st.session_state.current_step = "marketing"
                st.rerun()
        else:
            st.error("Please enter both company name and target audience")

def display_marketing_phase():
    """Display the marketing analysis phase"""
    st.subheader("📊 Marketing Analysis")
    
    if st.session_state.research_history:
        latest_research = st.session_state.research_history[-1]
        
        with st.spinner("Generating marketing analysis..."):
            marketing_data = asyncio.run(
                get_marketing_data(
                    latest_research["result"],
                    latest_research["company"],
                    st.session_state.current_audience
                )
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Brand Analysis")
                st.plotly_chart(create_audience_chart(marketing_data["result"]))
            
            with col2:
                st.markdown("### Market Position")
                # Add market position visualization here
                
            st.session_state.current_step = "campaign"
            st.rerun()
    else:
        st.info("Please complete the research phase first")

def display_campaign_generation():
    """Display campaign generation interface"""
    st.subheader("💡 Campaign Generation")
    
    if st.session_state.current_step == "campaign":
        campaigns = st.session_state.marketing_cache.get(
            f"marketing_{st.session_state.current_company}", {}
        ).get("result", [])
        
        if campaigns:
            for i, campaign in enumerate(campaigns):
                with st.expander(
                    f"Campaign {i+1}: {campaign.get('campaign_name', 'Untitled')}",
                    expanded=(i==0)
                ):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### Campaign Overview")
                        st.write(f"**Core Message:** {campaign.get('core_message', 'N/A')}")
                        st.write(f"**Visual Theme:** {campaign.get('visual_theme_description', 'N/A')}")
                        st.write(f"**Emotional Appeal:** {campaign.get('key_emotional_appeal', 'N/A')}")
                    
                    with col2:
                        st.markdown("#### Implementation")
                        st.write(f"**Timeline:** {campaign.get('campaign_timeline', 'N/A')}")
                        st.write(f"**Budget:** {campaign.get('budget_allocation', 'N/A')}")
                        st.write(f"**Success Metrics:** {campaign.get('success_metrics', 'N/A')}")
                    
                    if st.button(f"Generate Assets for Campaign {i+1}", key=f"gen_assets_{i}"):
                        st.session_state.current_step = "assets"
                        with st.spinner("Generating campaign assets..."):
                            assets = asyncio.run(
                                st.session_state.ad_orchestrator.generate_single_campaign(campaign)
                            )
                            st.session_state.ad_assets[f"campaign_{i}"] = assets
                            
                            if os.path.exists(assets['assets']['image']):
                                st.image(assets['assets']['image'], caption="Generated Campaign Image")
                            
                            with open(assets['assets']['tagline'], 'r') as f:
                                st.markdown("#### Campaign Tagline")
                                st.write(f.read())
                            
                            with open(assets['assets']['story'], 'r') as f:
                                st.markdown("#### Campaign Story")
                                st.write(f.read())
                            
                            st.download_button(
                                "Download Campaign Assets",
                                data=open(assets['assets']['details'], 'r').read(),
                                file_name=f"campaign_{i+1}_assets.json",
                                mime="application/json"
                            )

async def main():
    """Main application flow"""
    await initialize_agents()
    
    # Sidebar
    with st.sidebar:
        st.markdown("### Campaign Progress")
        display_progress()
        
        if st.session_state.research_history:
            st.markdown("### History")
            for item in st.session_state.research_history:
                with st.expander(f"{item['company']} - {item['timestamp'][:10]}"):
                    st.write(f"**Target:** {item['audience']}")
                    st.write(f"**Type:** {item['type']}")
    
    # Main content
    if st.session_state.current_step == "start":
        display_landing()
        display_research_phase()
    elif st.session_state.current_step == "research":
        display_research_phase()
    elif st.session_state.current_step == "marketing":
        display_marketing_phase()
    elif st.session_state.current_step in ["campaign", "assets"]:
        display_campaign_generation()

if __name__ == "__main__":
    asyncio.run(main())
