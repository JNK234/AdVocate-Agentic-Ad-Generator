"""
Claude LLM configuration and initialization.
"""
from typing import Optional
from langchain_anthropic import ChatAnthropic

def create_claude_llm(
    api_key: str,
    model_name: str = "claude-3-sonnet-20240229",
    temperature: float = 0.7,
) -> ChatAnthropic:
    """
    Create a Claude LLM instance.
    
    Args:
        api_key: Anthropic API key
        model_name: Name of the Claude model to use (default: claude-3-sonnet-20240229)
        temperature: Sampling temperature (default: 0.7)
        max_tokens: Maximum tokens to generate (optional)
    
    Returns:
        ChatAnthropic: Configured LLM instance
    """
    return ChatAnthropic(
        model=model_name,
        api_key=api_key,
        temperature=temperature,
    )
