from datetime import datetime
from threading import Lock
from uuid import uuid4

from app.database import SessionLocal
from app.graph.workflow import optimization_graph
from app.models.prompt import OptimizationSession, PromptVersion
from app.schemas.prompt import OptimizeResponse

jobs: dict[str, dict] = {}
jobs_lock = Lock()


def validate_history(result: dict) -> list[dict]:
    history = result.get("history") if isinstance(result, dict) else None
    if not history:
        raise ValueError("Optimization workflow completed without any iterations.")

    required_fields = {
        "iteration",
        "prompt",
        "output",
        "score",
        "failure_analysis",
        "scores",
    }
    required_scores = {
        "correctness",
        "clarity",
        "completeness",
        "conciseness",
    }

    for entry in history:
        if not isinstance(entry, dict) or not required_fields.issubset(entry):
            raise ValueError("Optimization workflow returned malformed history.")

        scores = entry["scores"]
        if not isinstance(scores, dict) or not required_scores.issubset(scores):
            raise ValueError("Optimization workflow returned malformed scores.")

    return history


def create_optimization_job() -> dict:
    now = datetime.utcnow().isoformat()
    job_id = str(uuid4())
    job = {
        "job_id": job_id,
        "status": "queued",
        "result": None,
        "error": None,
        "created_at": now,
        "updated_at": now,
    }

    with jobs_lock:
        jobs[job_id] = job

    return job.copy()


def get_optimization_job(job_id: str) -> dict | None:
    with jobs_lock:
        job = jobs.get(job_id)
        return job.copy() if job else None


def update_optimization_job(job_id: str, **changes) -> None:
    with jobs_lock:
        if job_id not in jobs:
            return

        jobs[job_id].update(changes)
        jobs[job_id]["updated_at"] = datetime.utcnow().isoformat()


def run_optimization(payload: dict) -> OptimizeResponse:
    result = optimization_graph.invoke({
        "task_type": payload["task_type"],
        "test_inputs": payload["test_inputs"],
        "current_prompt": payload["initial_prompt"],
        "current_output": "",
        "current_score": 0.0,
        "failure_analysis": "",
        "iteration": 1,
        "history": [],
        "should_stop": False,
    })
    history = validate_history(result)
    best = max(history, key=lambda x: x["score"])

    db = SessionLocal()
    try:
        session = OptimizationSession(
            task_type=payload["task_type"],
            initial_prompt=payload["initial_prompt"],
            final_prompt=best["prompt"],
            final_score=best["score"],
            total_iterations=len(history),
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        for entry in history:
            version = PromptVersion(
                session_id=session.id,
                iteration=entry["iteration"],
                prompt_text=entry["prompt"],
                output_text=entry["output"],
                score=entry["score"],
                failure_analysis=entry["failure_analysis"],
                correctness=entry["scores"]["correctness"],
                clarity=entry["scores"]["clarity"],
                completeness=entry["scores"]["completeness"],
                conciseness=entry["scores"]["conciseness"],
            )
            db.add(version)

        db.commit()

        return OptimizeResponse(
            session_id=session.id,
            final_prompt=best["prompt"],
            final_score=best["score"],
            total_iterations=len(history),
            history=history,
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def run_optimization_job(job_id: str, payload: dict) -> None:
    update_optimization_job(job_id, status="running", error=None)

    try:
        result = run_optimization(payload)
        update_optimization_job(
            job_id,
            status="completed",
            result=result.model_dump(),
            error=None,
        )
    except Exception as error:
        update_optimization_job(
            job_id,
            status="failed",
            result=None,
            error=str(error),
        )
