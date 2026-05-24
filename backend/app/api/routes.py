from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.prompt import OptimizeRequest, OptimizeResponse
from app.models.prompt import OptimizationSession, PromptVersion
from app.graph.workflow import optimization_graph
from app.auth import require_api_key

router = APIRouter(dependencies=[Depends(require_api_key)])


def validate_history(result: dict) -> list[dict]:
    history = result.get("history") if isinstance(result, dict) else None
    if not history:
        raise HTTPException(
            status_code=502,
            detail="Optimization workflow completed without any iterations."
        )

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
            raise HTTPException(
                status_code=502,
                detail="Optimization workflow returned malformed history."
            )

        scores = entry["scores"]
        if not isinstance(scores, dict) or not required_scores.issubset(scores):
            raise HTTPException(
                status_code=502,
                detail="Optimization workflow returned malformed scores."
            )

    return history


@router.post("/optimize", response_model=OptimizeResponse)
def optimize(request: OptimizeRequest, db: Session = Depends(get_db)):
    result = optimization_graph.invoke({
        "task_type": request.task_type,
        "test_input": request.test_input,
        "current_prompt": request.initial_prompt,
        "current_output": "",
        "current_score": 0.0, 
        "failure_analysis": "",
        "iteration": 1,
        "history": [],
        "should_stop": False
    })
    history = validate_history(result)
    best = max(history, key=lambda x: x["score"])

    session = OptimizationSession(
        task_type=request.task_type,
        initial_prompt=request.initial_prompt,
        final_prompt=best["prompt"],
        final_score=best["score"],
        total_iterations=len(history)
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
            conciseness=entry["scores"]["conciseness"]
        )
        db.add(version)
    db.commit()
 
    return OptimizeResponse(
        session_id=session.id,
        final_prompt=best["prompt"],
        final_score=best["score"],
        total_iterations=len(history),
        history=history
    )

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
