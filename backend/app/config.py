from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GROQ_API_KEY: str
    DATABASE_URL: str
    MAX_ITERATIONS: int = 7
    MIN_IMPROVEMENT_THRESHOLD: float = 0.05

    class Config:
        env_file = ".env"

settings = Settings()