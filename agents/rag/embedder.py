import os
from typing import List
from sentence_transformers import SentenceTransformer
import openai

class EmbeddingService:
    def __init__(self):
        self.provider = os.getenv("EMBEDDING_PROVIDER", "huggingface")
        
        if self.provider == "huggingface":
            # Using sentence-transformers locally (all-MiniLM-L6-v2 is small and fast)
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.dimension = 384
        elif self.provider == "openai":
            # Using OpenAI API
            self.client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model_name = "text-embedding-3-small"
            self.dimension = 1536
        else:
            raise ValueError(f"Unknown embedding provider: {self.provider}")

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
            
        if self.provider == "huggingface":
            # Encode locally (synchronous but fast enough for small batches)
            embeddings = self.model.encode(texts, batch_size=32)
            return embeddings.tolist()
            
        elif self.provider == "openai":
            response = await self.client.embeddings.create(
                input=texts,
                model=self.model_name
            )
            return [data.embedding for data in response.data]
