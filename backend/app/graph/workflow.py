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
    best_score: float
    best_iteration: int
    stale_iterations: int
    recent_improvements: list[float]
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
    # Normalize task-specific criteria into the canonical default criteria
    # so downstream logic can rely on `correctness`, `clarity`, `completeness`, and `conciseness`.
    SYNONYM_MAP = {
        "accuracy": "correctness",
        "coverage": "completeness",
        "readability": "clarity",
        "usefulness": "clarity",
        "relevance": "correctness",
        "confidence": "correctness",
        "efficiency": "conciseness",
        "fluency": "clarity",
        "adequacy": "completeness",
        "terminology": "clarity",
        "robustness": "correctness",
    }

    default_keys = ["correctness", "clarity", "completeness", "conciseness"]

    # Build a list of normalized score dicts where missing default keys are
    # filled by mapping synonyms or defaulting to 0.0.
    normalized_scores_list = []
    for j in judgments:
        scores = j.get("scores", {})
        normalized = {k: 0.0 for k in default_keys}
        for key, val in scores.items():
            if key in normalized:
                normalized[key] = val
            elif key in SYNONYM_MAP:
                mapped = SYNONYM_MAP[key]
                normalized[mapped] = val
        normalized_scores_list.append(normalized)

    # Average the normalized scores across test cases
    scores = {}
    for k in default_keys:
        scores[k] = sum(ns[k] for ns in normalized_scores_list) / len(normalized_scores_list)
    overall = sum(j["overall"] for j in judgments) / len(judgments)
    failure_analysis = "\n\n".join(
        f"Test case #{index}: {judgment['failure_analysis']}"
        for index, judgment in enumerate(judgments, start=1)
    )
    previous_best_score = state["best_score"]
    improvement = overall - previous_best_score
    is_new_best = overall > previous_best_score
    recent_improvements = (
        state["recent_improvements"] + [max(0.0, improvement)]
    )[-settings.IMPROVEMENT_WINDOW:]
    
    history_entry= {
        "iteration": state["iteration"],
        "prompt": state["current_prompt"],
        "output": state["current_output"],
        "score": overall,
        "improvement": improvement,
        "best_score": max(previous_best_score, overall),
        "failure_analysis": failure_analysis,
        "scores": scores
    }
    
    return {
        **state,
        "current_score": overall,
        "failure_analysis": failure_analysis,
        "history": state["history"] + [history_entry],
        "best_score": max(previous_best_score, overall),
        "best_iteration": state["iteration"] if is_new_best else state["best_iteration"],
        "stale_iterations": 0 if is_new_best else state["stale_iterations"] + 1,
        "recent_improvements": recent_improvements,
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
    if state["best_score"] >= settings.TARGET_SCORE:
        return "end"
    if state["iteration"] >= settings.MAX_ITERATIONS:
        return "end"
    if state["stale_iterations"] >= settings.PATIENCE_ITERATIONS:
        return "end"
    if len(state["recent_improvements"]) >= settings.IMPROVEMENT_WINDOW:
        average_improvement = sum(state["recent_improvements"]) / len(state["recent_improvements"])
        if average_improvement < settings.MIN_IMPROVEMENT_THRESHOLD:
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
