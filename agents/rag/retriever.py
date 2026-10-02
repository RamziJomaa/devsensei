import numpy as np
from typing import List, Dict, Any
from .embedder import EmbeddingService
from .indexer import QdrantIndexer
from qdrant_client.models import Filter, FieldCondition, MatchValue

class CodeRetriever:
    def __init__(self):
        self.embedder = EmbeddingService()
        self.dimension = self.embedder.dimension
        self.indexer = QdrantIndexer(vector_dimension=self.dimension)
        self.client = self.indexer.client
        self.collection_name = self.indexer.collection_name

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def _maximal_marginal_relevance(
        self, query_embedding: List[float], embeddings: List[List[float]], lambda_mult: float = 0.5, k: int = 4
    ) -> List[int]:
        """Calculates MMR to ensure both relevance to the query and diversity among the results."""
        if not embeddings:
            return []
            
        # Calculate similarity between query and all documents
        query_sims = [self._cosine_similarity(query_embedding, emb) for emb in embeddings]
        
        # Calculate similarity between all documents
        doc_sims = [[self._cosine_similarity(e1, e2) for e2 in embeddings] for e1 in embeddings]
        
        selected = []
        unselected = list(range(len(embeddings)))
        
        # Select first item based solely on query similarity
        best_idx = int(np.argmax(query_sims))
        selected.append(unselected.pop(best_idx))
        
        while len(selected) < k and unselected:
            best_score = -np.inf
            best_idx_in_unselected = -1
            
            for i, idx in enumerate(unselected):
                # Relevance to query
                relevance = query_sims[idx]
                
                # Diversity against already selected documents (max similarity to any selected)
                redundancy = max([doc_sims[idx][s_idx] for s_idx in selected]) if selected else 0
                
                # MMR formula: balance relevance and redundancy
                mmr_score = lambda_mult * relevance - (1 - lambda_mult) * redundancy
                
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx_in_unselected = i
            
            selected.append(unselected.pop(best_idx_in_unselected))
            
        return selected

    async def retrieve(self, query: str, repo_id: str, fetch_k: int = 15, final_k: int = 5) -> List[Dict[str, Any]]:
        # 1. Embed the natural language query
        query_embeddings = await self.embedder.embed_batch([query])
        query_vector = query_embeddings[0]

        # 2. Search Qdrant for top `fetch_k` most mathematically similar chunks
        search_result = await self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=Filter(
                must=[FieldCondition(key="repo_id", match=MatchValue(value=repo_id))]
            ),
            limit=fetch_k,
            with_vectors=True,
            with_payload=True
        )

        if not search_result:
            return []

        # 3. Apply MMR to rerank and filter down to `final_k` diverse chunks
        embeddings = [hit.vector for hit in search_result if hit.vector is not None]
        payloads = [hit.payload for hit in search_result]
        
        selected_indices = self._maximal_marginal_relevance(query_vector, embeddings, lambda_mult=0.6, k=final_k)
        
        return [payloads[i] for i in selected_indices]
