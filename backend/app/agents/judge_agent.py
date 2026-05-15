from groq import Groq
from app.config import settings
import json

client = Groq(api_key=settings.GROQ_API_KEY)

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

def run_judge_agent(task_type: str, system_prompt: str, test_input: str, output: str) -> dict:
    user_message = f"""Task type: {task_type}
System prompt used: {system_prompt}
Test input: {test_input}
Output produced: {output}

Score this output."""

    message = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=1024,
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
    )

    raw = message.choices[0].message.content
    return json.loads(raw)