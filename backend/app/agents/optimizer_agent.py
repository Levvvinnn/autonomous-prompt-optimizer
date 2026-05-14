import anthropic
from app.config import settings

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

OPTIMIZER_SYSTEM_PROMPT = """You are an expert prompt engineer.
You will be given a system prompt that is underperforming and a detailed failure analysis explaining exactly what is weak.
Rewrite the system prompt to fix those specific weaknesses.
Return ONLY the new system prompt text. No explanation, no preamble, no quotes."""

def run_optimizer_agent(current_prompt: str, failure_analysis: str, task_type: str) -> str:
    user_message = f"""Task type: {task_type}
Current system prompt: {current_prompt}
Failure analysis: {failure_analysis}

Rewrite the system prompt to fix these issues."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=OPTIMIZER_SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": user_message}
        ]
    )
    return message.content[0].text