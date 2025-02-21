"""
Claude LLM configuration and initialization.
"""
from typing import Optional
from langchain_openai import ChatOpenAI

def create_openai_llm(
    api_key: str,
    model_name: str = "gpt-4o-mini-2024-07-18",
    temperature: float = 0.7,
) -> ChatOpenAI:
    """
    Create a OpenaAI LLM instance.
    
    Args:
        api_key: OpenAI API key
        model_name: Name of the OpenAI model to use (default: gpt-4o-mini-2024-07-18)
        temperature: Sampling temperature (default: 0.7)
        max_tokens: Maximum tokens to generate (optional)
    
    Returns:
        ChatAnthropic: Configured LLM instance
    """
    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        temperature=temperature,
    )
