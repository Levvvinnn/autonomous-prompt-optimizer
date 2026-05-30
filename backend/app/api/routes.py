from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.prompt import OptimizeRequest, OptimizeJobResponse, JobStatusResponse
from app.models.prompt import OptimizationSession, PromptVersion
from app.auth import require_api_key
from app.rate_limit import rate_limit
from app.services.optimization import (
    create_optimization_job,
    get_optimization_job,
    run_optimization_job,
)

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.post(
    "/optimize",
    response_model=OptimizeJobResponse,
    dependencies=[Depends(rate_limit)],
)
def optimize(request: OptimizeRequest, background_tasks: BackgroundTasks):
    job = create_optimization_job()
    background_tasks.add_task(
        run_optimization_job,
        job["job_id"],
        request.model_dump(),
    )
    return OptimizeJobResponse(job_id=job["job_id"], status=job["status"])

@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job(job_id: str):
    job = get_optimization_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Optimization job not found.")
    return job

@router.get("/sessions")
def get_sessions(db: Session = Depends(get_db)):
    return db.query(OptimizationSession).order_by(
        OptimizationSession.created_at.desc()
    ).all()

@router.get("/sessions/{session_id}")
def get_session(session_id: int, db: Session = Depends(get_db)):
    versions = db.query(PromptVersion).filter(
        PromptVersion.session_id == session_id
    ).order_by(PromptVersion.iteration).all()
    return versions
