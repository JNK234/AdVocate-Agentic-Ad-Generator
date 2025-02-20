"""
Base agent implementation.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from langchain.agents import AgentExecutor, initialize_agent, AgentType
from langchain.chat_models import AzureChatOpenAI
from langchain.tools import Tool

class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    """
    def __init__(
        self,
        llm: AzureChatOpenAI,
        tools: List[Tool],
        agent_type: AgentType = AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose: bool = True
    ):
        """
        Initialize the base agent.
        
        Args:
            llm: Language model instance
            tools: List of tools available to the agent
            agent_type: Type of agent to initialize
            verbose: Whether to enable verbose logging
        """
        self.llm = llm
        self.tools = tools
        self.agent_type = agent_type
        self.verbose = verbose
        self.agent: Optional[AgentExecutor] = None
        
    async def initialize(self) -> None:
        """
        Initialize the agent with configured tools and LLM.
        """
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=self.agent_type,
            verbose=self.verbose,
            handle_parsing_errors=True
        )
        
        await self._post_initialize()
    
    @abstractmethod
    async def _post_initialize(self) -> None:
        """
        Hook for additional initialization steps in derived classes.
        """
        pass
    
    @abstractmethod
    async def run(self, input_text: str) -> str:
        """
        Run the agent with the given input.
        
        Args:
            input_text: Input text to process
            
        Returns:
            str: Agent's response
        """
        pass
