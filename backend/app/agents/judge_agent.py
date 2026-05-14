import anthropic
import json
from app.config import settings

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

JUDGE_SYSTEM_PROMPT = """You are an expert prompt evaluator. 
You will be given a task type, a system prompt, a test input, and the output that prompt produced.
Score the output and return ONLY a JSON object with no extra text, no markdown, no backticks.

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

All scores are between 0.0 and 1.0. Be harsh and specific in failure_analysis."""

def run_judge_agent(task_type: str, system_prompt: str, test_input: str, output: str) -> dict:
    user_message = f"""Task type: {task_type}
System prompt used: {system_prompt}
Test input: {test_input}
Output produced: {output}

Score this output."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=JUDGE_SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": user_message}
        ]
    )
    
    raw = message.content[0].text
    return json.loads(raw)