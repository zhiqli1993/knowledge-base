"""Chroma vector database client wrapper"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from mcp_server.config import ChromaConfig

class ChromaClient:
    def __init__(self, config: ChromaConfig):
        self.config = config
        # Use persistent client
        self.client = chromadb.Client(Settings(
            persist_directory=config.persist_directory,
            anonymized_telemetry=False
        ))
        self.collection = self.client.get_or_create_collection(
            name=config.collection_name
        )

    def add_documents(
        self,
        ids: List[str],
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]]
    ):
        """Add documents to Chroma collection"""
        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

    def query(
        self,
        query_embeddings: List[List[float]],
        n_results: int = 5,
        where: Optional[Dict] = None
    ) -> Dict:
        """Query Chroma collection"""
        return self.collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"]
        )

    def delete(self, ids: List[str]):
        """Delete documents by IDs"""
        self.collection.delete(ids=ids)

    def count(self) -> int:
        """Get document count"""
        return self.collection.count()
