from pydantic import BaseModel, Field, model_validator

class OptimizeRequest(BaseModel):
    task_type: str
    initial_prompt: str
    test_input: str | None = None
    test_inputs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_test_inputs(self):
        if self.test_input and not self.test_inputs:
            self.test_inputs = [self.test_input]

        self.test_inputs = [
            test_input.strip()
            for test_input in self.test_inputs
            if test_input.strip()
        ]

        if not self.test_inputs:
            raise ValueError("At least one test input is required.")

        return self

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

class OptimizeJobResponse(BaseModel):
    job_id: str
    status: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    result: OptimizeResponse | None = None
    error: str | None = None
    created_at: str
    updated_at: str
