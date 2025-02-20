"""
LLM configuration and initialization.
"""
from typing import Optional
from langchain.chat_models import AzureChatOpenAI
from ..config.settings import AzureSettings

def create_azure_llm(
    azure_settings: AzureSettings,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None
) -> AzureChatOpenAI:
    """
    Create an Azure OpenAI LLM instance.
    
    Args:
        azure_settings: Azure configuration settings
        temperature: Sampling temperature (default: 0.7)
        max_tokens: Maximum tokens to generate (optional)
    
    Returns:
        AzureChatOpenAI: Configured LLM instance
    """
    return AzureChatOpenAI(
        deployment_name=azure_settings.deployment_name,
        openai_api_base=azure_settings.api_base,
        openai_api_key=azure_settings.api_key,
        openai_api_version=azure_settings.api_version,
        temperature=temperature,
        max_tokens=max_tokens
    )
