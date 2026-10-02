from fastapi import FastAPI
from .routers import analysis, health, ask, webhook
from .metrics import metrics_endpoint

app = FastAPI(
    title="DevSensei API",
    description="Agentic AI GitHub Review System",
    version="0.1.0"
)

app.include_router(health.router)
app.include_router(analysis.router)
app.include_router(ask.router)
app.include_router(webhook.router)

@app.get("/metrics")
async def get_metrics():
    return metrics_endpoint()

@app.get("/")
async def root():
    return {"message": "DevSensei backend is running. Visit /docs for the API schema."}
