from langgraph.graph import StateGraph, END
from .state import GraphState
from .code_review_agent import CodeReviewAgent
from .rag_agent import RAGAgent
from .devops_agent import DevOpsAgent
from .aggregator_agent import AggregatorAgent
from .eval_agent import EvalAgent

def create_devsensei_graph():
    """Compiles the multi-agent execution graph."""
    workflow = StateGraph(GraphState)
    
    # Initialize node instances
    code_reviewer = CodeReviewAgent()
    rag_agent = RAGAgent()
    devops_agent = DevOpsAgent()
    aggregator = AggregatorAgent()
    evaluator = EvalAgent()

    # Add nodes to graph
    workflow.add_node("code_reviewer", code_reviewer.run)
    workflow.add_node("rag_agent", rag_agent.run)
    workflow.add_node("devops_agent", devops_agent.run)
    workflow.add_node("aggregator", aggregator.run)
    workflow.add_node("eval_node", evaluator.run)
    
    # Define linear execution flow for simplicity
    workflow.set_entry_point("code_reviewer")
    workflow.add_edge("code_reviewer", "rag_agent")
    workflow.add_edge("rag_agent", "devops_agent")
    workflow.add_edge("devops_agent", "aggregator")
    # Add eval_node after aggregator as requested
    workflow.add_edge("aggregator", "eval_node")
    workflow.add_edge("eval_node", END)
    
    return workflow.compile()
