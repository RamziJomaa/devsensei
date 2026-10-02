from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
import hmac
import hashlib
import os
import uuid
from sqlalchemy.future import select

from backend.database import AsyncSessionLocal
from backend.models import Repository, Analysis, AnalysisStatus
from backend.worker import run_analysis_background

router = APIRouter(prefix="/api/v1/webhook", tags=["Webhook"])

async def verify_signature(request: Request):
    """Verifies that the webhook actually came from GitHub using the HMAC SHA-256 signature."""
    secret = os.getenv("GITHUB_WEBHOOK_SECRET")
    if not secret:
        # Bypass if running locally without secrets configured
        return True
        
    signature_header = request.headers.get("X-Hub-Signature-256")
    if not signature_header:
        raise HTTPException(status_code=401, detail="Missing X-Hub-Signature-256 header")
        
    body = await request.body()
    hash_object = hmac.new(secret.encode("utf-8"), msg=body, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + hash_object.hexdigest()
    
    if not hmac.compare_digest(expected_signature, signature_header):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

@router.post("/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    await verify_signature(request)
    
    event = request.headers.get("X-GitHub-Event")
    if event != "pull_request":
        return {"status": "ignored", "reason": f"Event {event} is not supported. We only listen to pull_request."}
        
    payload = await request.json()
    action = payload.get("action")
    
    # We trigger analysis when a PR is opened or updated (synchronized)
    if action not in ["opened", "synchronize"]:
        return {"status": "ignored", "reason": f"Action {action} ignored"}
        
    repo_url = payload.get("repository", {}).get("html_url")
    pr_number = payload.get("pull_request", {}).get("number")
    
    if not repo_url:
        raise HTTPException(status_code=400, detail="Missing repository URL in payload")

    # DB Operations to register the Analysis immediately
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Repository).where(Repository.url == repo_url))
        repo = result.scalars().first()
        if not repo:
            repo = Repository(url=repo_url, name=repo_url.split("/")[-1])
            db.add(repo)
            await db.commit()
            await db.refresh(repo)
            
        analysis = Analysis(repo_id=repo.id, status=AnalysisStatus.PENDING, triggered_by=f"webhook_pr_{pr_number}")
        db.add(analysis)
        await db.commit()
        await db.refresh(analysis)
        
        analysis_id = analysis.id

    # Queue the background task. This allows the FastAPI endpoint to instantly return 200 OK.
    background_tasks.add_task(run_analysis_background, analysis_id, repo_url)
    
    return {"status": "accepted", "message": "Analysis queued successfully", "analysis_id": str(analysis_id)}
