from typing import List, Dict
from langchain.agents import AgentType
from langchain.tools import Tool
from src.agents.base import BaseAgent
from src.core.llm import create_azure_llm
from .graph import build_graph

def parse_research_results(research_results: str) -> Dict[str, str]:
    """
    Parse research results and extract company summary, target audience, and brand values.
    
    Args:
        research_results: Research results string
        
    Returns:
        Dict[str, str]: Dictionary containing company summary, target audience, and brand values
    """
    company_summary = ""
    # target_audience = "" # Already provided as input
    # brand_values = "" # Extract from analysis
    
    try:
        # Split the research results into sections
        sections = research_results.split("Analysis:")
        
        # Extract raw findings
        raw_findings = sections[0].split("Raw Findings:")[1].strip()
        
        # Extract analysis
        analysis = sections[1].strip()
        
        company_summary = raw_findings[:500] # Limit to 500 characters
        
        return {
            "company_summary": company_summary,
            "analysis": analysis
        }
    except Exception as e:
        print(f"Error parsing research results: {str(e)}")
        return {
            "company_summary": "",
            "analysis": ""
        }

class MarketingAgent(BaseAgent):
    """
    Agent specialized in marketing campaign generation.
    """
    def __init__(
        self,
        llm,
        tools: List[Tool] = [],
        model_name: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        agent_type: AgentType = AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose: bool = True
    ):
        """
        Initialize the marketing agent.
        
        Args:
            llm: Language model instance
            tools: List of tools available to the agent
            model_name: Name of the model to use
            temperature: Sampling temperature
            agent_type: Type of agent to initialize
            verbose: Whether to enable verbose logging
        """
        super().__init__(llm, tools, agent_type, verbose)
        
    async def _post_initialize(self) -> None:
        """
        Additional initialization steps for marketing agent.
        """
        self.graph = await build_graph(self.llm, self.agent)
    
    async def run(self, company_summary: str, target_audience: str, brand_values: str) -> str:
        """
        Run the marketing agent with the given input.
        
        Args:
            company_summary: Summary of the company
            target_audience: Target audience for the campaign
            brand_values: Brand values of the company
            
        Returns:
            str: Agent's generated campaign ideas
        """
        if not self.agent:
            raise RuntimeError("Agent not initialized. Call initialize() first.")
        
        try:
            # Run LangGraph graph
            inputs = {"company_summary": company_summary, "target_audience": target_audience, "brand_values": brand_values}
            results = await self.graph.ainvoke(inputs)
            
            # Extract results from the graph state
            campaign_ideas = results.get("campaign_ideas")
            
            return campaign_ideas
            
        except Exception as e:
            return f"Error during campaign generation: {str(e)}"
