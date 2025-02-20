from typing import Dict, Any
from langchain.chat_models import AzureChatOpenAI
from langchain.agents import AgentExecutor
from langgraph.graph import StateGraph, END
from .nodes import GraphNodes
from .types import GraphState

async def build_graph(llm: AzureChatOpenAI, agent_executor: AgentExecutor) -> StateGraph:
    """
    Build the workflow graph for ad campaign generation.
    
    Args:
        llm: Language model instance
        agent_executor: Agent executor instance
        
    Returns:
        StateGraph: Compiled workflow graph
    """
    # Initialize graph nodes
    nodes = GraphNodes(llm, agent_executor)
    
    # Create graph with typed state
    workflow = StateGraph(GraphState)
    
    # Add nodes to graph
    workflow.add_node("analyze_strategy_node", nodes.analyze_strategy)
    workflow.add_node("creative_direction_node", nodes.generate_creative_direction)
    workflow.add_node("campaign_assets_node", nodes.generate_campaign_assets)
    workflow.add_node("quality_check_node", nodes.quality_check)
    
    # Define conditional edge for quality check
    def should_regenerate(state: GraphState) -> str:
        """Determine if assets need to be regenerated based on quality check."""
        assets = state.get("campaign_assets", [])
        if not assets:
            return "campaign_assets"
            
        for asset in assets:
            quality_check = asset.get("quality_check", "")
            if "fail" in quality_check.lower() or "error" in quality_check.lower():
                return "campaign_assets"
                
        return "end"

    # Define edges
    workflow.add_edge("analyze_strategy_node", "creative_direction_node")
    workflow.add_edge("creative_direction_node", "campaign_assets_node")
    workflow.add_edge("campaign_assets_node", END)
    
    # Add conditional edge from quality check
    workflow.add_conditional_edges(
        "quality_check_node",
        should_regenerate,
        {
            "campaign_assets": "campaign_assets_node",
            "end": END
        }
    )
    
    # Set entry point
    workflow.set_entry_point("analyze_strategy_node")
    
    # Compile graph
    return workflow.compile()
