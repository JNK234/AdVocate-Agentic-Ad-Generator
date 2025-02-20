"""
Research agent implementation.
"""
from typing import Dict, List
from langchain.agents import AgentType
from langchain.tools import Tool
# from langchain_anthropic import ChatAnthropic
from src.agents.base import BaseAgent
from src.agents.research.prompts import RESEARCH_AGENT_PROMPT, QUESTION_GENERATION_PROMPT, DATA_ANALYSIS_PROMPT
from src.agents.research.graph import build_graph
from src.core.claude_llm import create_claude_llm
from .nodes import GraphNodes

class ResearchAgent(BaseAgent):
    """
    Agent specialized in company research and analysis.
    """
    def __init__(
        self,
        llm,
        tools: List[Tool],
        model_name: str = "claude-3-sonnet-20240229",
        temperature: float = 0.7,
        agent_type: AgentType = AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose: bool = True
    ):
        """
        Initialize the research agent.
        
        Args:
            api_key: Anthropic API key
            tools: List of tools available to the agent
            model_name: Name of the Claude model to use
            temperature: Sampling temperature
            agent_type: Type of agent to initialize
            verbose: Whether to enable verbose logging
        """
        
        super().__init__(llm, tools, agent_type, verbose)
        self.research_chain = RESEARCH_AGENT_PROMPT
        self.question_chain = QUESTION_GENERATION_PROMPT
        self.analysis_chain = DATA_ANALYSIS_PROMPT
        
    async def _post_initialize(self) -> None:
        """
        Additional initialization steps for research agent.
        """
        self.nodes = GraphNodes(self.llm, self.agent)
        self.graph = await build_graph(self.llm, self.agent)
    
    async def run(self, company_name: str, target_audience: str) -> str:
        """
        Run the research agent with the given input.
        
        Args:
            input_text: Input text describing the research task
            
        Returns:
            str: Agent's research findings
        """
        if not self.agent:
            raise RuntimeError("Agent not initialized. Call initialize() first.")
        
        try:
            # Run LangGraph graph
            inputs = {"company_name": company_name, "target_audience": target_audience}
            results = await self.graph.ainvoke(inputs)
            
            # Extract results from the graph state
            questions = results.get("research_questions")
            raw_findings = results.get("raw_findings")
            analysis = results.get("analysis")
            
            # Combine results
            final_report = (
                f"Research Questions:\n{questions}\n\n"
                f"Raw Findings:\n{raw_findings}\n\n"
                f"Analysis:\n{analysis}"
            )
            
            return final_report
            
        except Exception as e:
            return f"Error during research: {str(e)}"
