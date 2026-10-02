import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.rag.retriever import CodeRetriever
from agents.rag.chain import RAGChain
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Hardcoded test data representing typical developer questions
REPO_ID = "test-repo-123"
QUESTIONS = [
    "How does the authentication system generate JWT tokens?",
    "Where is the database connection initialized?",
    "What algorithms are used for code chunking in the RAG pipeline?",
    "How does the GitHub service handle rate limiting?",
    "What is the endpoint for fetching an analysis report?"
]

async def evaluate_faithfulness(question: str, context: str, answer: str) -> float:
    """LLM-as-a-judge faithfulness evaluator."""
    eval_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an impartial AI evaluator. You will receive a question, a codebase context, and an AI-generated answer. "
                   "Your task is to determine if the answer is completely FAITHFUL to the context. That means every technical claim made in the answer "
                   "must be explicitly supported by the context. You must output ONLY a single number between 0.0 and 1.0 representing the faithfulness score. Output absolutely nothing else."),
        ("user", "Question: {question}\n\nContext:\n{context}\n\nAnswer:\n{answer}\n\nFaithfulness Score (0.0 to 1.0):")
    ])
    
    # Using a strict LLM specifically for the judge persona
    llm = ChatGroq(model_name="llama3-8b-8192", temperature=0)
    chain = eval_prompt | llm | StrOutputParser()
    
    score_str = await chain.ainvoke({
        "question": question,
        "context": context,
        "answer": answer
    })
    
    try:
        return float(score_str.strip())
    except ValueError:
        return 0.0

async def main():
    print(f"Starting RAG Evaluation for repo: {REPO_ID}")
    retriever = CodeRetriever()
    chain = RAGChain()
    
    total_faithfulness = 0.0
    
    for idx, q in enumerate(QUESTIONS):
        print(f"\n--- Evaluation {idx+1}/{len(QUESTIONS)} ---")
        print(f"Q: {q}")
        
        try:
            # 1. Retrieve
            chunks = await retriever.retrieve(q, REPO_ID)
            if not chunks:
                print("⚠️ No chunks retrieved. Ensure indexer has run for this REPO_ID.")
                continue
                
            # 2. Generate
            result = await chain.answer(q, chunks)
            print(f"A: {result.answer}")
            print(f"Cited Files: {[c.file_path for c in result.cited_chunks]}")
            
            # 3. Evaluate Faithfulness
            context_str = "\n".join([c.get('content', '') for c in chunks])
            faithfulness = await evaluate_faithfulness(q, context_str, result.answer)
            print(f"RAGAS Faithfulness Score: {faithfulness}")
            
            total_faithfulness += faithfulness
        except Exception as e:
            print(f"Error during evaluation: {str(e)}")
        
    print(f"\n==========================")
    if total_faithfulness > 0:
        print(f"Average System Faithfulness Score: {total_faithfulness / len(QUESTIONS):.2f}")
    
if __name__ == "__main__":
    asyncio.run(main())
