from typing import Dict, Optional, TypedDict
from langgraph.graph import StateGraph, END
from langchain.chat_models import AzureChatOpenAI
from .nodes import GraphState, MarketingNodes

async def build_graph(llm: AzureChatOpenAI, agent):
    builder = StateGraph(GraphState)
    
    # Initialize nodes
    nodes = MarketingNodes(llm, agent)
    
    # Add nodes
    builder.add_node("analyze_company", nodes.analyze_company)
    builder.add_node("generate_campaigns", nodes.generate_campaigns)
    
    # Add edges
    builder.add_edge("analyze_company", "generate_campaigns")
    builder.add_edge("generate_campaigns", END)
    
    # Set entry point
    builder.set_entry_point("analyze_company")
    
    return builder.compile()
