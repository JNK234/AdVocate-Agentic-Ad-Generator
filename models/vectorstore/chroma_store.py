"""
ChromaDB vector storage implementation.
"""
import os
from datetime import datetime
from typing import Dict, List, Optional, Union
import chromadb
from chromadb.config import Settings
from .base import BaseVectorStore

class ChromaStore(BaseVectorStore):
    """ChromaDB implementation of vector storage."""
    
    def __init__(self, persist_directory: str = "models/vectorstore/data"):
        """
        Initialize ChromaDB with persistent storage.
        
        Args:
            persist_directory: Directory for persistent storage
        """
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        self.client = chromadb.Client(
            Settings(
                persist_directory=persist_directory,
                is_persistent=True
            )
        )
    
    def _get_collection(self, session_id: str):
        """Get or create a collection for the session."""
        return self.client.get_or_create_collection(
            name=session_id,
            metadata={"timestamp": datetime.utcnow().isoformat()}
        )
    
    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, str]]] = None,
        session_id: Optional[str] = None
    ) -> List[str]:
        """
        Add texts to ChromaDB.
        
        Args:
            texts: List of text strings to add
            metadatas: Optional list of metadata dictionaries
            session_id: Session identifier (used as collection name)
            
        Returns:
            List[str]: List of IDs for the added texts
        """
        if not session_id:
            session_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            
        collection = self._get_collection(session_id)
        
        # Generate IDs for the documents
        ids = [f"{session_id}_{i}" for i in range(len(texts))]
        
        # Ensure each text has corresponding metadata
        if not metadatas:
            metadatas = [{} for _ in texts]
        
        # Add timestamp to metadata
        for metadata in metadatas:
            metadata["timestamp"] = datetime.utcnow().isoformat()
            metadata["session_id"] = session_id
        
        # Add to ChromaDB
        collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        return ids
    
    def _process_filter(self, filter_metadata: Dict[str, any]) -> Dict[str, any]:
        """
        Process filter metadata into ChromaDB's expected format.
        
        Args:
            filter_metadata: Filter metadata dictionary
            
        Returns:
            Dict[str, any]: Processed filter in ChromaDB format
        """
        if not filter_metadata:
            return None
            
        # If filter already contains 'where' clause, use it directly
        if "where" in filter_metadata:
            return filter_metadata["where"]
            
        # Convert simple key-value pairs to ChromaDB format
        where_clause = {}
        for key, value in filter_metadata.items():
            if isinstance(value, dict):
                # Already in ChromaDB format
                where_clause[key] = value
            else:
                # Convert to ChromaDB format
                where_clause[key] = {"$eq": value}
        
        return where_clause
    
    def search(
        self,
        query: str,
        k: int = 4,
        session_id: Optional[str] = None,
        filter_metadata: Optional[Dict[str, Union[str, Dict]]] = None
    ) -> List[Dict[str, any]]:
        """
        Search for similar texts in ChromaDB.
        
        Args:
            query: Query text to search for
            k: Number of results to return
            session_id: Optional session to search within
            filter_metadata: Optional metadata filters
            
        Returns:
            List[Dict[str, any]]: List of search results with scores
        """
        # Process filter metadata
        where_clause = self._process_filter(filter_metadata)
        
        if session_id:
            collection = self._get_collection(session_id)
            results = collection.query(
                query_texts=[query],
                n_results=k,
                where=where_clause
            )
            return self._format_results(results)
        else:
            # Search across all collections if no session_id provided
            results = []
            for collection_name in self.client.list_collections():
                collection = self.client.get_collection(collection_name)
                try:
                    collection_results = collection.query(
                        query_texts=[query],
                        n_results=k,
                        where=where_clause
                    )
                    results.extend(self._format_results(collection_results))
                except Exception as e:
                    print(f"Error querying collection {collection_name}: {str(e)}")
                    continue
            
            # Sort by distance and take top k
            results = sorted(results, key=lambda x: x["distance"])[:k]
            
            return results
    
    def _format_results(self, results: Dict) -> List[Dict[str, any]]:
        """Format ChromaDB results into a standard format."""
        formatted_results = []
        for i in range(len(results["ids"][0])):
            formatted_results.append({
                "id": results["ids"][0][i],
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i]
            })
        return formatted_results
    
    def get_collection_stats(self, session_id: Optional[str] = None) -> Dict[str, any]:
        """
        Get statistics about the ChromaDB collection.
        
        Args:
            session_id: Optional session to get stats for
            
        Returns:
            Dict[str, any]: Collection statistics
        """
        if session_id:
            collection = self._get_collection(session_id)
            return {
                "count": collection.count(),
                "metadata": collection.metadata
            }
        else:
            stats = {}
            for collection_name in self.client.list_collections():
                collection = self.client.get_collection(collection_name)
                stats[collection_name] = {
                    "count": collection.count(),
                    "metadata": collection.metadata
                }
            return stats
