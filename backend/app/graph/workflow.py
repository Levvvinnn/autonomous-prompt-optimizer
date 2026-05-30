from typing import TypedDict
from langgraph.graph import StateGraph, END
from app.agents.task_agent import run_task_agent
from app.agents.judge_agent import run_judge_agent
from app.agents.optimizer_agent import run_optimizer_agent
from app.config import settings

class OptimizationState(TypedDict):
    task_type: str
    test_inputs: list[str]
    current_prompt: str
    current_output: str
    current_score: float
    failure_analysis: str
    iteration: int
    history: list
    should_stop: bool

def task_node(state: OptimizationState) -> OptimizationState:
    outputs = [
        run_task_agent(
            system_prompt=state["current_prompt"],
            test_input=test_input,
        )
        for test_input in state["test_inputs"]
    ]
    combined_output = "\n\n".join(
        f"Test case #{index}\n{output}"
        for index, output in enumerate(outputs, start=1)
    )
    return {**state, "current_output": combined_output}

def judge_node(state: OptimizationState) -> OptimizationState:
    judgments = []

    for index, test_input in enumerate(state["test_inputs"], start=1):
        marker = f"Test case #{index}\n"
        output = state["current_output"].split(marker, maxsplit=1)[-1]
        if index < len(state["test_inputs"]):
            next_marker = f"\n\nTest case #{index + 1}\n"
            output = output.split(next_marker, maxsplit=1)[0]

        judgments.append(run_judge_agent(
            task_type=state["task_type"],
            system_prompt=state["current_prompt"],
            test_input=test_input,
            output=output,
        ))

    scores = {
        "correctness": sum(j["scores"]["correctness"] for j in judgments) / len(judgments),
        "clarity": sum(j["scores"]["clarity"] for j in judgments) / len(judgments),
        "completeness": sum(j["scores"]["completeness"] for j in judgments) / len(judgments),
        "conciseness": sum(j["scores"]["conciseness"] for j in judgments) / len(judgments),
    }
    overall = sum(j["overall"] for j in judgments) / len(judgments)
    failure_analysis = "\n\n".join(
        f"Test case #{index}: {judgment['failure_analysis']}"
        for index, judgment in enumerate(judgments, start=1)
    )
    
    history_entry= {
        "iteration": state["iteration"],
        "prompt": state["current_prompt"],
        "output": state["current_output"],
        "score": overall,
        "failure_analysis": failure_analysis,
        "scores": scores
    }
    
    return {
        **state,
        "current_score": overall,
        "failure_analysis": failure_analysis,
        "history": state["history"] + [history_entry]
    }

def optimizer_node(state: OptimizationState) -> OptimizationState:
    new_prompt=run_optimizer_agent(
        current_prompt=state["current_prompt"],
        failure_analysis=state["failure_analysis"],
        task_type=state["task_type"]
    )
    return {
        **state,
        "current_prompt": new_prompt,
        "iteration": state["iteration"] + 1
    }

def should_continue(state: OptimizationState) -> str:
    if state["current_score"] >= 0.95:
        return "end"
    if state["iteration"] >= settings.MAX_ITERATIONS:
        return "end"
    if len(state["history"]) > 1:
        prev_score = state["history"][-2]["score"]
        improvement = state["current_score"] - prev_score
        if improvement<settings.MIN_IMPROVEMENT_THRESHOLD:
            return "end"
    return "continue"

def build_graph():
    graph = StateGraph(OptimizationState)
    
    graph.add_node("task", task_node)
    graph.add_node("judge", judge_node)
    graph.add_node("optimizer", optimizer_node)
    
    graph.set_entry_point("task")
    graph.add_edge("task", "judge")
    graph.add_conditional_edges(
        "judge",
        should_continue,
        {
            "continue": "optimizer",
            "end": END
        }
    )
    graph.add_edge("optimizer", "task")
    
    return graph.compile()

optimization_graph = build_graph()
