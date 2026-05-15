from groq import Groq
from app.config import settings

client = Groq(api_key=settings.GROQ_API_KEY)

OPTIMIZER_SYSTEM_PROMPT = """You are an expert prompt engineer.
You will be given a system prompt that is underperforming and a detailed failure analysis explaining exactly what is weak.
Rewrite the system prompt to fix those specific weaknesses.
Return ONLY the new system prompt text. No explanation, no preamble, no quotes."""

def run_optimizer_agent(current_prompt: str, failure_analysis: str, task_type: str) -> str:
    user_message = f"""Task type: {task_type}
Current system prompt: {current_prompt}
Failure analysis: {failure_analysis}

Rewrite the system prompt to fix these issues."""

    message = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=1024,
        messages=[
            {"role": "system", "content": OPTIMIZER_SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
    )
    return message.choices[0].message.content