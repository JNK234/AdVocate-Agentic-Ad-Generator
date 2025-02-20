"""
Configuration settings and environment variable management.
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class AzureSettings:
    """Azure OpenAI settings."""
    api_key: str
    api_base: str
    api_version: str
    deployment_name: str

@dataclass
class Settings:
    """Global settings configuration."""
    azure: AzureSettings
    tavily_api_key: str
    claude_api_key: str

def load_settings() -> Settings:
    """
    Load settings from environment variables.
    
    Returns:
        Settings: Configuration settings object
    
    Raises:
        ValueError: If required environment variables are missing
    """
    load_dotenv()
    
    # Required environment variables
    required_vars = [
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_API_BASE",
        "AZURE_OPENAI_API_VERSION",
        "AZURE_OPENAI_DEPLOYMENT_NAME",
        "TAVILY_API_KEY",
        "CLAUDE_API_KEY"
    ]
    
    # Check for missing environment variables
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    # Create Azure settings
    azure_settings = AzureSettings(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_base=os.getenv("AZURE_OPENAI_API_BASE"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    )
    
    # Create global settings
    settings = Settings(
        azure=azure_settings,
        tavily_api_key=os.getenv("TAVILY_API_KEY"),
        claude_api_key=os.getenv("CLAUDE_API_KEY")
    )
    
    return settings
