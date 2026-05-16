import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.graph.workflow import optimization_graph

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "running"}

@app.get("/health")
def health():
    return {"status": "ok"}

from app.agents.task_agent import run_task_agent
from app.agents.judge_agent import run_judge_agent
from app.agents.optimizer_agent import run_optimizer_agent

@app.get("/test-agents")
def test_agents():
    output = run_task_agent(
        system_prompt="Summarize the following text briefly.",
        test_input="The mitochondria is the powerhouse of the cell. It produces ATP through cellular respiration."
    )
    judgment = run_judge_agent(
        task_type="summarization",
        system_prompt="Summarize the following text briefly.",
        test_input="The mitochondria is the powerhouse of the cell.",
        output=output
    )
    optimized = run_optimizer_agent(
        current_prompt="Summarize the following text briefly.",
        failure_analysis=judgment["failure_analysis"],
        task_type="summarization"
    )
    return {
        "task_output": output,
        "judgment": judgment,
        "optimized_prompt": optimized
    }


@app.get("/test-loop")
def test_loop():
    result = optimization_graph.invoke({
        "task_type": "summarization",
        "test_input": "The mitochondria is the powerhouse of the cell. It produces ATP through cellular respiration. This process occurs in the inner membrane of the mitochondria.",
        "current_prompt": "Summarize the following text.",
        "current_output": "",
        "current_score": 0.0,
        "failure_analysis": "",
        "iteration": 1,
        "history": [],
        "should_stop": False
    })
    return {
        "final_prompt": result["current_prompt"],
        "final_score": result["current_score"],
        "total_iterations": result["iteration"],
        "history": result["history"]
    }