from pydantic import BaseModel

class OptimizeRequest(BaseModel):
    task_type: str
    initial_prompt: str
    test_input: str

class IterationResponse(BaseModel):
    iteration: int
    prompt: str
    output: str
    score: float
    failure_analysis: str

class OptimizeResponse(BaseModel):
    session_id: int
    final_prompt: str
    final_score: float
    total_iterations: int
    history: list