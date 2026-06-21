"""Judge agent: evaluates outputs and returns structured scores.

This agent selects scoring criteria based on the `task_type`. The default
criteria are `correctness`, `clarity`, `completeness`, and `conciseness`,
but many task types use specialized criteria defined in `TASK_CRITERIA`.
"""

from groq import Groq
from app.config import settings
import json
from pydantic import BaseModel, Field, ValidationError

client = Groq(api_key=settings.GROQ_API_KEY)
MAX_JUDGE_ATTEMPTS = 3

# Mapping of task types to the judge criteria to use for scoring.
# Add task-specific criteria here as needed.
DEFAULT_CRITERIA = [
    "correctness",
    "clarity",
    "completeness",
    "conciseness",
]

TASK_CRITERIA: dict[str, list[str]] = {
    "summarization": ["accuracy", "conciseness", "coverage", "readability"],
    "classification": ["correctness", "confidence", "clarity", "robustness"],
    "translation": ["accuracy", "fluency", "adequacy", "terminology"],
    "code_generation": ["correctness", "efficiency", "readability", "robustness"],
}

JUDGE_SYSTEM_PROMPT = """You are an expert prompt evaluator.
You will be given a task type, a system prompt, a test input, and the output it produced.
Score the output and return ONLY a JSON object. No markdown, no backticks, no extra text whatsoever.

Return exactly this structure:
{
  "scores": {
    "correctness": 0.0,
    "clarity": 0.0,
    "completeness": 0.0,
    "conciseness": 0.0
  },
  "overall": 0.0,
  "failure_analysis": "specific explanation of what was weak and why"
}

All scores between 0.0 and 1.0. Be harsh and specific."""


def build_system_prompt(criteria: list[str]) -> str:
    """Construct a system prompt that instructs the judge to return the given criteria.

    The prompt is intentionally strict: the model must return only a JSON object
    with a `scores` mapping containing the listed criteria.
    """
    scores_obj = ",\n    ".join([f'"{c}": 0.0' for c in criteria])
    return (
        "You are an expert prompt evaluator.\n"
        "Return ONLY a JSON object with the following structure:\n"
        "{\n  \"scores\": {\n    "
        + scores_obj
        + "\n  },\n  \"overall\": 0.0,\n  \"failure_analysis\": \"...\"\n}\n"
        "All scores between 0.0 and 1.0. Be specific and concise."
    )


def _example_criteria_usage():
    """Small helper demonstrating how criteria are selected for task types.

    This is non-essential at runtime but useful for quick manual checks.
    """
    examples = ["summarization", "classification", "translation", "unknown"]
    return {t: TASK_CRITERIA.get(t, DEFAULT_CRITERIA) for t in examples}


class JudgeScores(BaseModel):
    correctness: float = Field(ge=0.0, le=1.0)
    clarity: float = Field(ge=0.0, le=1.0)
    completeness: float = Field(ge=0.0, le=1.0)
    conciseness: float = Field(ge=0.0, le=1.0)


class JudgeResult(BaseModel):
    scores: JudgeScores
    overall: float = Field(ge=0.0, le=1.0)
    failure_analysis: str


def extract_json_object(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Judge response did not contain a JSON object.")

    return json.loads(raw[start:end + 1])


def validate_scores_dict(scores: dict, expected: list[str]) -> None:
    """Ensure the `scores` mapping contains the expected keys and values are 0.0-1.0."""
    if not isinstance(scores, dict):
        raise ValueError("`scores` must be a JSON object mapping criteria to numbers.")

    missing = [k for k in expected if k not in scores]
    if missing:
        raise ValueError(f"Missing expected score keys: {missing}")

    for k, v in scores.items():
        if not isinstance(v, (int, float)):
            raise ValueError(f"Score for {k} is not numeric: {v}")
        if v < 0.0 or v > 1.0:
            raise ValueError(f"Score for {k} out of range: {v}")


def parse_judgment(raw: str, expected_criteria: list[str] | None = None) -> dict:
    payload = extract_json_object(raw)

    # Basic structure validation
    if "scores" not in payload or "overall" not in payload or "failure_analysis" not in payload:
        raise ValueError("Judge response missing required top-level fields.")

    scores = payload["scores"]
    expected = expected_criteria or DEFAULT_CRITERIA
    validate_scores_dict(scores, expected)

    overall = payload["overall"]
    if not isinstance(overall, (int, float)) or overall < 0.0 or overall > 1.0:
        raise ValueError("`overall` score missing or out of range.")

    if not isinstance(payload["failure_analysis"], str):
        raise ValueError("`failure_analysis` must be a string.")

    return payload


def fallback_judgment(error: Exception, expected_criteria: list[str] | None = None) -> dict:
    expected = expected_criteria or DEFAULT_CRITERIA
    scores = {k: 0.0 for k in expected}
    return {
        "scores": scores,
        "overall": 0.0,
        "failure_analysis": (
            "The judge model did not return valid scoring JSON after "
            f"{MAX_JUDGE_ATTEMPTS} attempts. Last error: {error}"
        ),
    }


def run_judge_agent(task_type: str, system_prompt: str, test_input: str, output: str) -> dict:
    # Determine which criteria to use for this task type
    criteria = TASK_CRITERIA.get(task_type, DEFAULT_CRITERIA)
    logger.info("Judge running for task_type=%s using criteria=%s", task_type, criteria)

    user_message = f"""Task type: {task_type}
System prompt used: {system_prompt}
Test input: {test_input}
Output produced: {output}

Score this output according to: {', '.join(criteria)}"""

    last_error: Exception | None = None
    system = build_system_prompt(criteria)
    for attempt in range(MAX_JUDGE_ATTEMPTS):
        retry_hint = ""
        if attempt > 0:
            retry_hint = "\n\nYour previous response was invalid. Return only the JSON object."

        message = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1024,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_message + retry_hint}
            ]
        )

        raw = message.choices[0].message.content
        try:
            return parse_judgment(raw, expected_criteria=criteria)
        except (json.JSONDecodeError, ValidationError, ValueError) as error:
            last_error = error
            logger.warning("Judge parsing failed on attempt %s: %s", attempt + 1, error)

    return fallback_judgment(last_error or ValueError("Unknown judge parsing error."), expected_criteria=criteria)
