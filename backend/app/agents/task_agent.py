from groq import Groq
from app.config import settings

client = Groq(api_key=settings.GROQ_API_KEY)

def run_task_agent(system_prompt: str, test_input: str) -> str:
    message = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=1024,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": test_input}
        ]
    )
    return message.choices[0].message.content