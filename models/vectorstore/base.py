"""
Base interface for vector storage implementations.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

class BaseVectorStore(ABC):
    """Base class for vector storage implementations."""
    
    @abstractmethod
    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, str]]] = None,
        session_id: Optional[str] = None
    ) -> List[str]:
        """
        Add texts to the vector store.
        
        Args:
            texts: List of text strings to add
            metadatas: Optional list of metadata dictionaries
            session_id: Optional session identifier
            
        Returns:
            List[str]: List of IDs for the added texts
        """
        pass
    
    @abstractmethod
    def search(
        self,
        query: str,
        k: int = 4,
        session_id: Optional[str] = None,
        filter_metadata: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, any]]:
        """
        Search for similar texts in the vector store.
        
        Args:
            query: Query text to search for
            k: Number of results to return
            session_id: Optional session to search within
            filter_metadata: Optional metadata filters
            
        Returns:
            List[Dict[str, any]]: List of search results with scores
        """
        pass
    
    @abstractmethod
    def get_collection_stats(self, session_id: Optional[str] = None) -> Dict[str, any]:
        """
        Get statistics about the vector store collection.
        
        Args:
            session_id: Optional session to get stats for
            
        Returns:
            Dict[str, any]: Collection statistics
        """
        pass
