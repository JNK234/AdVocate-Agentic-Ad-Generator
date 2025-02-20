"""
Research agent node functions.
"""
from typing import Dict, Optional, TypedDict
from langchain_anthropic import ChatAnthropic
from langchain.tools import Tool
from .prompts import RESEARCH_AGENT_PROMPT, QUESTION_GENERATION_PROMPT, DATA_ANALYSIS_PROMPT

class GraphState(TypedDict):
    company_name: str
    target_audience: str
    research_questions: Optional[str]
    raw_findings: Optional[str]
    analysis: Optional[str]


class GraphNodes:
    def __init__(self, llm: ChatAnthropic, agent):
        self.llm = llm
        self.agent = agent

    async def generate_questions(self, state: GraphState) -> Dict:
        company_name = state['company_name']
        target_audience = state['target_audience']
        response = await self.llm.ainvoke(
            QUESTION_GENERATION_PROMPT.format_messages(company_name=company_name, target_audience=target_audience)
        )
        
        print("Generated Questions")
        print(response.content)
        
        
        return {"research_questions": response.content}
        
    async def retrieve_data(self, state: GraphState) -> Dict:
        company_name = state['company_name']
        target_audience = state['target_audience']
        input_text = f"{company_name} for {target_audience}"
        raw_findings = await self.agent.arun(
            RESEARCH_AGENT_PROMPT.format(input=input_text)
        )
        return {"raw_findings": raw_findings}
        
    async def analyze_data(self, state: GraphState) -> Dict:
        raw_findings = state['raw_findings']
        response = await self.llm.apredict_messages(
            DATA_ANALYSIS_PROMPT.format_messages(collected_data=raw_findings)
        )
        return {"analysis": response.content}
