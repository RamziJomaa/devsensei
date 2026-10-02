from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

# 1. Standard API Metrics
REQUEST_COUNT = Counter(
    'devsensei_request_count', 
    'Total number of requests', 
    ['endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'devsensei_request_latency_seconds', 
    'Request latency in seconds', 
    ['endpoint']
)

# 2. Agent Execution Metrics
AGENT_RUN_DURATION = Histogram(
    'devsensei_agent_run_duration_seconds', 
    'Time taken for an individual agent to complete its run', 
    ['agent_name']
)

# 3. LLMOps Cost & Usage Metrics
LLM_TOKEN_COUNT = Counter(
    'devsensei_llm_token_count', 
    'Number of LLM tokens consumed', 
    ['agent_name', 'model']
)

# 4. LLMOps Quality Metrics
RAG_FAITHFULNESS_SCORE = Gauge(
    'devsensei_rag_faithfulness_score', 
    'Latest RAGAS/LLM-as-a-judge faithfulness score for an analysis'
)

# 5. System Orchestration
ACTIVE_ANALYSES = Gauge(
    'devsensei_active_analyses', 
    'Number of analysis pipelines currently running in the background'
)

def metrics_endpoint():
    """Generates the prometheus metrics payload for the /metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
