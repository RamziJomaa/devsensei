import os
from typing import List
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from .models import CodeChunk

class QdrantIndexer:
    def __init__(self, vector_dimension: int):
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        qdrant_api_key = os.getenv("QDRANT_API_KEY", None)
        
        self.client = AsyncQdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        self.collection_name = "devsensei_codebase"
        self.dimension = vector_dimension

    async def initialize_collection(self):
        """Creates the collection if it doesn't already exist."""
        collections = await self.client.get_collections()
        exists = any(c.name == self.collection_name for c in collections.collections)
        
        if not exists:
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.dimension, distance=Distance.COSINE),
            )

    async def upsert_chunks(self, chunks: List[CodeChunk], embeddings: List[List[float]]):
        """Upserts a batch of code chunks and their embeddings into Qdrant."""
        if not chunks or not embeddings or len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings must be provided and have the same length.")

        points = []
        for chunk, vector in zip(chunks, embeddings):
            points.append(
                PointStruct(
                    id=chunk.id,  # Must be UUID format
                    vector=vector,
                    payload={
                        "repo_id": chunk.repo_id,
                        "file_path": chunk.file_path,
                        "content": chunk.content,
                        "chunk_type": chunk.chunk_type,
                        "start_line": chunk.start_line,
                        "end_line": chunk.end_line,
                        "language": chunk.language
                    }
                )
            )
            
        await self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

    async def delete_repo_chunks(self, repo_id: str):
        """Deletes all chunks belonging to a specific repository to allow clean re-indexing."""
        await self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="repo_id",
                        match=MatchValue(value=repo_id)
                    )
                ]
            )
        )
