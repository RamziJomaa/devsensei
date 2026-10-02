from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sys
import os

# Ensure agents are accessible if importing from the top-level
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.rag.retriever import CodeRetriever
from agents.rag.chain import RAGChain, RAGResponse

router = APIRouter(prefix="/api/v1", tags=["RAG"])

class AskRequest(BaseModel):
    question: str
    repo_id: str

@router.post("/ask", response_model=RAGResponse)
async def ask_codebase(request: AskRequest):
    retriever = CodeRetriever()
    chain = RAGChain()
    
    try:
        # Retrieve chunks using Semantic Search + MMR
        chunks = await retriever.retrieve(query=request.question, repo_id=request.repo_id)
        if not chunks:
            return RAGResponse(
                answer="No relevant codebase context found for this repository. It may not be indexed yet.",
                cited_chunks=[],
                confidence=0.0
            )
            
        # Generate answer securely constrained by context
        result = await chain.answer(question=request.question, chunks=chunks)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
