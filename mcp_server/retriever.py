from typing import List, Optional
from mcp_server.config import Config
from mcp_server.models import SearchResult
from mcp_server.chroma_client import ChromaClient
from mcp_server.embeddings import OllamaEmbeddings


class Retriever:
    def __init__(self, config: Config):
        self.config = config
        self.chroma = ChromaClient(config.chroma)
        self.embeddings = OllamaEmbeddings(config.ollama)

    async def search(
        self,
        query: str,
        n_results: int = 5,
        source_filter: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Perform semantic search on knowledge base

        Args:
            query: Natural language search query
            n_results: Maximum number of results to return
            source_filter: Optional source type filter ('github', 'web_page', 'web_site')

        Returns:
            List of SearchResult objects sorted by relevance
        """
        # Generate query embedding
        query_embedding = await self.embeddings.embed(query)

        # Build where filter
        where_filter = None
        if source_filter:
            where_filter = {
                "source_id": {"$contains": source_filter}
            }

        # Query Chroma
        results = self.chroma.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter
        )

        # Format results
        search_results = []

        if not results['ids'] or not results['ids'][0]:
            return search_results

        for i in range(len(results['ids'][0])):
            chunk_id = results['ids'][0][i]
            text = results['documents'][0][i]
            metadata = results['metadatas'][0][i]
            distance = results['distances'][0][i]

            # Convert distance to score (lower distance = higher score)
            # Using simple inverse: score = 1 / (1 + distance)
            score = 1.0 / (1.0 + distance)

            search_result = SearchResult(
                chunk_id=chunk_id,
                text=text,
                score=score,
                source_id=metadata.get('source_id', ''),
                file_path=metadata.get('file_path', ''),
                metadata=metadata
            )

            search_results.append(search_result)

        return search_results

    def format_results(self, results: List[SearchResult]) -> str:
        """
        Format search results for display

        Args:
            results: List of SearchResult objects

        Returns:
            Formatted string for display
        """
        if not results:
            return "No results found."

        output = []
        output.append(f"Found {len(results)} results:\n")

        for i, result in enumerate(results, 1):
            output.append(f"--- Result {i} (score: {result.score:.3f}) ---")
            output.append(f"Source: {result.source_id}")
            output.append(f"File: {result.file_path}")
            output.append(f"\n{result.text}\n")

        return "\n".join(output)