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


def parse_judgment(raw: str) -> dict:
    payload = extract_json_object(raw)
    return JudgeResult.model_validate(payload).model_dump()


def fallback_judgment(error: Exception) -> dict:
    return JudgeResult(
        scores=JudgeScores(
            correctness=0.0,
            clarity=0.0,
            completeness=0.0,
            conciseness=0.0,
        ),
        overall=0.0,
        failure_analysis=(
            "The judge model did not return valid scoring JSON after "
            f"{MAX_JUDGE_ATTEMPTS} attempts. Last error: {error}"
        ),
    ).model_dump()


def run_judge_agent(task_type: str, system_prompt: str, test_input: str, output: str) -> dict:
    user_message = f"""Task type: {task_type}
System prompt used: {system_prompt}
Test input: {test_input}
Output produced: {output}

Score this output."""

    last_error: Exception | None = None
    for attempt in range(MAX_JUDGE_ATTEMPTS):
        retry_hint = ""
        if attempt > 0:
            retry_hint = "\n\nYour previous response was invalid. Return only the JSON object."

        message = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1024,
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": user_message + retry_hint}
            ]
        )

        raw = message.choices[0].message.content
        try:
            return parse_judgment(raw)
        except (json.JSONDecodeError, ValidationError, ValueError) as error:
            last_error = error

    return fallback_judgment(last_error or ValueError("Unknown judge parsing error."))
