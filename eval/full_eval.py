import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.graph import create_devsensei_graph

async def run_full_eval():
    print("Initializing DevSensei Graph for Full Pipeline Evaluation...")
    app = create_devsensei_graph()
    
    # Mocking initial state with some injected findings to test the Eval node
    initial_state = {
        "analysis_id": "test-analysis-001",
        "repo_url": "https://github.com/langchain-ai/langgraph",
        "repo_id": "langchain-ai/langgraph",
        "file_tree": [],
        "pr_diff": None,
        "messages": [],
        "findings": [
            {
                "title": "Hardcoded AWS Secret",
                "severity": "critical",
                "description": "Found a hardcoded AWS_SECRET_KEY in utils/auth.py",
                "suggestion": "Extract the key to an environment variable or secrets manager."
            },
            {
                "title": "Vague Error Handling",
                "severity": "low",
                "description": "Exception caught but only printed to console.",
                "suggestion": "Use structured logging to track exceptions."
            }
        ],
        "report_draft": "",
        "eval_scores": {},
        "status": "running",
        "error": None
    }
    
    print("\n--- Executing Multi-Agent Graph ---")
    final_state = await app.ainvoke(initial_state)
    
    print("\n--- Final Aggregated Report Draft ---")
    print(final_state.get("report_draft"))
    
    print("\n--- Automated EvalAgent Scores (LLM-as-a-Judge) ---")
    scores = final_state.get("eval_scores", {})
    for metric, val in scores.items():
        print(f"{metric}: {val}")
        
    print("\n--- RAGAS Integration Note ---")
    print("In a CI pipeline, RAGAS metrics (Faithfulness, Answer Relevancy, Context Precision) ")
    print("are calculated across an explicit dataset of Ground Truths using `from ragas import evaluate`.")
    print("The EvalAgent acts as an inline sanity check, while RAGAS runs offline benchmarking.")

if __name__ == "__main__":
    asyncio.run(run_full_eval())
