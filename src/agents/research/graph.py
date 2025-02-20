"""
LangGraph graph definition for the research agent.
"""
from typing import Dict, Optional, TypedDict
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from .nodes import GraphState, GraphNodes

async def build_graph(llm: ChatAnthropic, agent):
    builder = StateGraph(GraphState)
    
    # Initialize nodes
    nodes = GraphNodes(llm, agent)
    
    # Add nodes without lambdas
    builder.add_node("generate_questions", nodes.generate_questions)
    builder.add_node("retrieve_data", nodes.retrieve_data) 
    builder.add_node("analyze_data", nodes.analyze_data)
    
    # Rest remains the same
    builder.add_edge("generate_questions", "retrieve_data")
    builder.add_edge("retrieve_data", "analyze_data")
    builder.add_edge("analyze_data", END)
    
    builder.set_entry_point("generate_questions")
    return builder.compile()
