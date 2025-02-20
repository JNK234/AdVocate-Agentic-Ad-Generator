import asyncio
import os
import streamlit as st
from datetime import datetime

from src.agents.research.agent import ResearchAgent
from marketing_strategy_agent import MarketingAgent
from src.agents.AdGen.orchestrator import AdCampaignOrchestrator
from src.agents.AdGen.ad_content_generator import CreativeAgent
from src.core.llm import create_llm
from src.config.settings import load_settings
from src.core.tools import create_tavily_tool
from langchain.agents import AgentType
from models.vectorstore import ChromaStore

# Initialize ChromaDB
vectorstore = ChromaStore()

# LLM and Agent setup
settings = load_settings()
llm = create_llm(azure_settings=settings.azure)

# Initialize tools
search_tool = create_tavily_tool(api_key=settings.tavily_api_key)
tools = [search_tool]

# Initialize creative agent and orchestrator
creative_agent = CreativeAgent(llm=llm)
ad_orchestrator = AdCampaignOrchestrator(creative_agent=creative_agent)

# Initialize research agent
research_agent = ResearchAgent(
    llm=llm,
    tools=tools,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    vectorstore=vectorstore
)
research_agent.initialize()

marketing_agent = MarketingAgent(
    llm=llm,
    tools=tools,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    vectorstore=vectorstore,
)
marketing_agent.initialize()

async def get_research_data(company: str, audience: str, force_new: bool = False):
    """
    Two-tier cache check:
    1. Check session cache (for active session)
    2. Check ChromaDB (for persistent storage)
    3. Run research agent if needed
    """
    cache_key = f"{company}_{audience}"
    
    # Check session cache first (fastest)
    if not force_new and cache_key in st.session_state.research_cache:
        return {
            "result": st.session_state.research_cache[cache_key]["result"],
            "source": "session_cache",
            "timestamp": st.session_state.research_cache[cache_key]["timestamp"]
        }
    
    # Check ChromaDB if not in session
    if not force_new:
        chroma_results = vectorstore.search(
            query=company,
            k=1,
            filter_metadata={
                "where": {
                    "$and": [
                        {"company_name": {"$eq": company}},
                        {"content_type": {"$eq": "analysis"}}
                    ]
                }
            }
        )
        
        if chroma_results:
            # Found in ChromaDB, cache in session and return
            research_data = {
                "result": chroma_results[0]['document'],
                "timestamp": chroma_results[0]['metadata']['timestamp'],
                "source": "chroma_cache"
            }
            # Cache in session for future use
            st.session_state.research_cache[cache_key] = research_data
            return research_data
    
    # No cache hit, run research agent
    if force_new:
        prompt = f"Conduct fresh research for {company} targeting {audience}. Focus on market size, customer needs, and potential strategies."
    else:
        prompt = f"Research market opportunities and strategies for {company} targeting {audience}. Focus on market size, customer needs, and potential strategies."
    
    new_research = await research_agent.run(prompt)
    
    # Cache the new results in both session and ChromaDB
    research_data = {
        "result": new_research,
        "timestamp": datetime.utcnow().isoformat(),
        "source": "new_research"
    }
    
    # Update session cache
    st.session_state.research_cache[cache_key] = research_data
    
    return research_data

async def get_marketing_data(research_result: str, company: str, force_new: bool = False):
    """
    Similar two-tier caching for marketing analysis
    """
    cache_key = f"marketing_{company}"
    
    # Check session cache
    if not force_new and cache_key in st.session_state.marketing_cache:
        return {
            "result": st.session_state.marketing_cache[cache_key]["result"],
            "source": "session_cache",
            "timestamp": st.session_state.marketing_cache[cache_key]["timestamp"]
        }
    
    # Check ChromaDB
    if not force_new:
        chroma_results = vectorstore.search(
            query=company,
            k=1,
            filter_metadata={
                "where": {
                    "$and": [
                        {"company_name": {"$eq": company}},
                        {"content_type": {"$eq": "marketing_analysis"}}
                    ]
                }
            }
        )
        
        if chroma_results:
            marketing_data = {
                "result": chroma_results[0]['document'],
                "timestamp": chroma_results[0]['metadata']['timestamp'],
                "source": "chroma_cache"
            }
            st.session_state.marketing_cache[cache_key] = marketing_data
            return marketing_data
    
    # Generate new marketing analysis
    new_marketing = await marketing_agent.run(research_result)
    
    marketing_data = {
        "result": new_marketing,
        "timestamp": datetime.utcnow().isoformat(),
        "source": "new_analysis"
    }
    
    # Update session cache
    st.session_state.marketing_cache[cache_key] = marketing_data
    
    return marketing_data

def run_analysis(company, audience, force_new=False):
    """Synchronous wrapper for the async analysis functions"""
    return asyncio.run(get_research_data(company, audience, force_new))

def run_marketing(research_result, company, force_new=False):
    """Synchronous wrapper for the async marketing function"""
    return asyncio.run(get_marketing_data(research_result, company, force_new))

# Set page config
st.set_page_config(page_title="AI Marketing Research & Ad Generator", layout="wide")

# Title
st.title("AI Marketing Research & Ad Generator")

# Initialize session state
if 'research_cache' not in st.session_state:
    st.session_state.research_cache = {}
if 'marketing_cache' not in st.session_state:
    st.session_state.marketing_cache = {}
if 'research_history' not in st.session_state:
    st.session_state.research_history = []
if 'current_company' not in st.session_state:
    st.session_state.current_company = ""
if 'current_audience' not in st.session_state:
    st.session_state.current_audience = ""
if 'ad_assets' not in st.session_state:
    st.session_state.ad_assets = {}
if 'session_id' not in st.session_state:
    st.session_state.session_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

# Create tabs
research_tab, marketing_tab = st.tabs(["Research", "Marketing & Ads"])

with research_tab:
    # Input fields
    col1, col2 = st.columns(2)
    with col1:
        company = st.text_input("Target Company", key="company")
    with col2:
        audience = st.text_input("Target Audience", key="audience")

    # Go ahead button
    if st.button("Go Ahead"):
        if company and audience:
            st.session_state.current_company = company
            st.session_state.current_audience = audience
            
            with st.spinner("Retrieving/Generating Research..."):
                research_data = run_analysis(company, audience)
                
                # Show source of data
                if research_data["source"] == "session_cache":
                    st.success("Retrieved from current session!")
                elif research_data["source"] == "chroma_cache":
                    st.info(f"Retrieved from previous analysis ({research_data['timestamp']})")
                elif research_data["source"] == "new_research":
                    st.info("Generated new research!")
                else:
                    st.error(research_data["result"])
                    st.stop()
                
                # Option to force new research
                if research_data["source"] != "new_research":
                    if st.button("Generate Fresh Research"):
                        with st.spinner("Generating fresh research..."):
                            research_data = run_analysis(company, audience, force_new=True)
                
                # Store in history
                st.session_state.research_history.append({
                    "type": "research",
                    "company": company,
                    "audience": audience,
                    "result": research_data["result"],
                    "source": research_data["source"],
                    "timestamp": research_data["timestamp"]
                })
        else:
            st.error("Please enter both company and audience")

    # Follow-up research section
    if st.session_state.research_history:
        st.subheader("Follow-up Research")
        follow_up = st.text_area("Enter additional research questions or aspects to explore")
        
        if st.button("Do More Research"):
            if follow_up:
                prompt = f"Given the target company {company} and target audience {audience}, {follow_up}"
                with st.spinner("Conducting follow-up research..."):
                    result = asyncio.run(research_agent.run(prompt))
                    st.session_state.research_history.append({
                        "type": "follow_up",
                        "company": company,
                        "audience": audience,
                        "query": follow_up,
                        "result": result,
                        "timestamp": datetime.utcnow().isoformat()
                    })
            else:
                st.error("Please enter a follow-up question")

with marketing_tab:
    if st.session_state.research_history:
        st.subheader("Marketing Analysis & Ad Generation")
        
        # Get latest research
        latest_research = st.session_state.research_history[-1]
        company = latest_research["company"]
        
        if st.button("Generate Marketing Content"):
            with st.spinner("Analyzing and generating marketing content..."):
                marketing_data = run_marketing(
                    latest_research["result"],
                    company
                )
                
                # Show source of data
                if marketing_data["source"] == "session_cache":
                    st.success("Retrieved marketing analysis from current session!")
                elif marketing_data["source"] == "chroma_cache":
                    st.info(f"Retrieved marketing analysis from cache ({marketing_data['timestamp']})")
                else:
                    st.success("Generated new marketing analysis!")
                
                marketing_result = marketing_data["result"]
                    
                # Option to force new analysis
                if marketing_data["source"] != "new_analysis":
                    if st.button("Generate Fresh Marketing Analysis"):
                        with st.spinner("Generating fresh marketing analysis..."):
                            marketing_data = run_marketing(
                                latest_research["result"],
                                company,
                                force_new=True
                            )
                
                # Display marketing results
                marketing_result = marketing_data["result"]
                
                # Display campaigns and generate ads
                if isinstance(marketing_result, list):
                    for i, campaign in enumerate(marketing_result):
                            with st.expander(f"Campaign {i+1}: {campaign.get('campaign_name', 'Untitled')}", expanded=i==0):
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.subheader("Campaign Overview")
                                    st.write(f"**Core Message:** {campaign.get('core_message', 'N/A')}")
                                    
                                    st.subheader("Visual Theme")
                                    visual_theme = campaign.get('visual_theme_description', {})
                                    if isinstance(visual_theme, dict):
                                        st.write(f"- Color Palette: {visual_theme.get('color_palette', 'N/A')}")
                                        st.write(f"- Style: {visual_theme.get('photography_illustration_style', 'N/A')}")
                                        st.write(f"- Key Elements: {visual_theme.get('key_visual_elements', 'N/A')}")
                                        st.write(f"- Mood: {visual_theme.get('mood_and_atmosphere', 'N/A')}")
                                    else:
                                        st.write(visual_theme)
                                    
                                    st.subheader("Emotional Appeal")
                                    emotional_appeal = campaign.get('key_emotional_appeal', {})
                                    if isinstance(emotional_appeal, dict):
                                        st.write(f"- Primary Emotion: {emotional_appeal.get('primary_emotion', 'N/A')}")
                                        st.write(f"- Psychological Triggers: {emotional_appeal.get('supporting_psychological_triggers', 'N/A')}")
                                        st.write(f"- Desired Reaction: {emotional_appeal.get('desired_audience_reaction', 'N/A')}")
                                    else:
                                        st.write(emotional_appeal)
                                
                                with col2:
                                    st.subheader("Social Media Strategy")
                                    social_focus = campaign.get('social_media_focus', {})
                                    if isinstance(social_focus, dict):
                                        st.write(f"- Primary Platforms: {social_focus.get('primary_platforms', 'N/A')}")
                                        st.write(f"- Content Format: {social_focus.get('content_format_recommendations', 'N/A')}")
                                        st.write(f"- Engagement Tactics: {social_focus.get('engagement_tactics', 'N/A')}")
                                        st.write(f"- Hashtag Strategy: {social_focus.get('hashtag_strategy', 'N/A')}")
                                    else:
                                        st.write(social_focus)
                                    
                                    st.subheader("Implementation Details")
                                    st.write(f"**Campaign Timeline:** {campaign.get('campaign_timeline', 'N/A')}")
                                    st.write(f"**Success Metrics:** {campaign.get('success_metrics', 'N/A')}")
                                    st.write(f"**Budget Allocation:** {campaign.get('budget_allocation', 'N/A')}")
                                    st.write(f"**Risk Mitigation:** {campaign.get('risk_mitigation', 'N/A')}")
                                
                                # Display prompt suggestions
                                st.subheader("AI Image Generation Prompts")
                                prompt_suggestions = campaign.get('prompt_suggestions', {})
                                if prompt_suggestions:
                                    tabs = st.tabs(["Product Focus", "Brand Focus", "Social Media"])
                                    
                                    with tabs[0]:
                                        st.text_area("Product-Focused Prompt", 
                                                    prompt_suggestions.get('product_focused', ''),
                                                    height=100,
                                                    key=f"product_prompt_{i}")
                                    
                                    with tabs[1]:
                                        st.text_area("Brand-Focused Prompt",
                                                    prompt_suggestions.get('brand_focused', ''),
                                                    height=100,
                                                    key=f"brand_prompt_{i}")
                                    
                                    with tabs[2]:
                                        st.text_area("Social Media Prompt",
                                                    prompt_suggestions.get('social_media', ''),
                                                    height=100,
                                                    key=f"social_prompt_{i}")
                                
                                # Ad Generation Section
                                st.subheader("Ad Generation")
                                if st.button(f"Generate Ad Assets for Campaign {i+1}", key=f"gen_ad_{i}"):
                                    with st.spinner("Generating ad assets..."):
                                        # Generate assets for this campaign
                                        assets = asyncio.run(ad_orchestrator.generate_single_campaign(campaign))
                                        st.session_state.ad_assets[f"campaign_{i}"] = assets
                                        
                                        # Display generated assets
                                        st.success("Ad assets generated successfully!")
                                        
                                        try:
                                            # Display image if available
                                            if os.path.exists(assets['assets']['image']):
                                                st.image(assets['assets']['image'], caption="Generated Campaign Image")
                                            
                                            # Display tagline
                                            with open(assets['assets']['tagline'], 'r') as f:
                                                st.subheader("Campaign Tagline")
                                                st.write(f.read())
                                            
                                            # Display story
                                            with open(assets['assets']['story'], 'r') as f:
                                                st.subheader("Campaign Story")
                                                st.write(f.read())
                                            
                                            # Add download buttons
                                            st.download_button(
                                                label="Download Campaign Details",
                                                data=open(assets['assets']['details'], 'r').read(),
                                                file_name=f"campaign_{i+1}_details.json",
                                                mime="application/json"
                                            )
                                        except (FileNotFoundError, IOError) as e:
                                            st.error(f"Error accessing generated files: {str(e)}")
    else:
        st.info("Please conduct research first in the Research tab!")

# Display research history
if st.session_state.research_history:
    st.sidebar.title("Research History")
    
    for i, item in enumerate(st.session_state.research_history):
        with st.sidebar.expander(
            f"{item['type'].title()} - {item['company']}",
            expanded=(i == len(st.session_state.research_history) - 1)
        ):
            st.write(f"**Timestamp:** {item['timestamp']}")
            st.write(f"**Target Audience:** {item.get('audience', 'N/A')}")
            if item['type'] == 'follow_up':
                st.write(f"**Question:** {item['query']}")
            st.write("**Results:**")
            st.write(item['result'])
