"""
Core tools configuration and initialization.
"""
import requests
from typing import Dict, List
from langchain.tools import Tool

def create_tavily_tool(api_key: str) -> Tool:
    """
    Create a Tavily search tool.
    
    Args:
        api_key: Tavily API key
    
    Returns:
        Tool: Configured Tavily search tool
    """
    def search_tavily(query: str) -> str:
        """
        Search using Tavily API.
        
        Args:
            query: Search query string
        
        Returns:
            str: Formatted search results
        
        Raises:
            Exception: If API request fails
        """
        url = "https://api.tavily.com/search"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload: Dict = {
            "query": query,
            "num_results": 10,
            "include_domains": [],  # Optional domain filtering
            "exclude_domains": [],  # Optional domain exclusion
            "search_depth": "advanced"  # Use advanced search for better results
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            results: List[Dict] = data["results"]
            
            # Format results with title, content snippet, and URL
            formatted_results = []
            for res in results[:5]:  # Limit to top 5 results
                formatted_results.append(
                    f"Title: {res['title']}\n"
                    f"Content: {res.get('content', 'No content available')}\n"
                    f"URL: {res['url']}\n"
                )
            
            return "\n\n".join(formatted_results)
            
        except Exception as e:
            return f"Error querying Tavily API: {str(e)}"
    
    return Tool(
        name="Tavily Search",
        func=search_tavily,
        description="Search the web for information on any topic using Tavily's advanced search API."
    )
