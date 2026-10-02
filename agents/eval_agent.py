from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_groq import ChatGroq
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.state import GraphState

class FindingEval(BaseModel):
    relevance_score: float = Field(description="Score 0.0-1.0: is this finding actually about the codebase context and not hallucinated?")
    severity_accuracy: float = Field(description="Score 0.0-1.0: does the assigned severity match the description?")
    actionability_score: float = Field(description="Score 0.0-1.0: does the finding include a specific suggestion?")

class EvalScores(BaseModel):
    findings_evals: List[FindingEval]
    avg_finding_relevance: float
    avg_actionability: float

class EvalAgent:
    def __init__(self):
        # We use a strict, fast model for the judging persona
        self.llm = ChatGroq(model_name="llama3-8b-8192", temperature=0)
        self.parser = JsonOutputParser(pydantic_object=EvalScores)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an impartial AI-as-a-judge system evaluating the quality of code review findings.\n\n"
                       "You must score each finding strictly based on the rubric.\n\n"
                       "Format Instructions:\n{format_instructions}"),
            ("user", "Evaluate the following findings generated for repository {repo_id}:\n\n{findings}")
        ])
        self.chain = self.prompt | self.llm | self.parser

    async def run(self, state: GraphState) -> GraphState:
        """Evaluates findings in the state and attaches scores."""
        findings = state.get("findings", [])
        
        if not findings:
            # If no findings, assume perfect actionability, 0 relevance
            state["eval_scores"] = {
                "avg_finding_relevance": 0.0,
                "avg_actionability": 1.0,
            }
            return state

        try:
            eval_result = await self.chain.ainvoke({
                "repo_id": state.get("repo_id", "unknown"),
                "findings": str(findings),
                "format_instructions": self.parser.get_format_instructions()
            })
            
            # Use dictionary keys to match Pydantic BaseModel output parsing
            evals = eval_result.get("findings_evals", [])
            
            if evals:
                avg_rel = sum([e.get("relevance_score", 0.0) for e in evals]) / len(evals)
                avg_act = sum([e.get("actionability_score", 0.0) for e in evals]) / len(evals)
            else:
                avg_rel, avg_act = 0.0, 0.0
            
            eval_scores = state.get("eval_scores", {})
            eval_scores["avg_finding_relevance"] = avg_rel
            eval_scores["avg_actionability"] = avg_act
            
            state["eval_scores"] = eval_scores
            
        except Exception as e:
            print(f"EvalAgent error during scoring: {e}")
            eval_scores = state.get("eval_scores", {})
            eval_scores["error"] = str(e)
            state["eval_scores"] = eval_scores
            
        return state
