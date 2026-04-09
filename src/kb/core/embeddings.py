import httpx
from typing import List
from kb.config import OllamaConfig


class OllamaEmbeddings:
    def __init__(self, config: OllamaConfig):
        self.config = config
        self.base_url = f"http://{config.host}:{config.port}"
        self.client = httpx.AsyncClient(timeout=config.timeout)

    async def embed(self, text: str) -> List[float]:
        """Generate embedding for single text"""
        response = await self.client.post(
            f"{self.base_url}/api/embeddings",
            json={
                "model": self.config.model,
                "prompt": text
            }
        )
        response.raise_for_status()
        return response.json()["embedding"]

    async def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> List[List[float]]:
        """Generate embeddings for batch of texts"""
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = []
            for text in batch:
                embedding = await self.embed(text)
                batch_embeddings.append(embedding)
            embeddings.extend(batch_embeddings)
        return embeddings

    async def check_model_available(self) -> bool:
        """Check if embedding model is available"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            models = response.json().get("models", [])
            return any(m["name"] == self.config.model for m in models)
        except Exception:
            return False

    async def pull_model(self):
        """Pull embedding model if not available"""
        response = await self.client.post(
            f"{self.base_url}/api/pull",
            json={"name": self.config.model}
        )
        response.raise_for_status()

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()