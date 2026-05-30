from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GROQ_API_KEY: str
    DATABASE_URL: str
    MAX_ITERATIONS: int = 7
    TARGET_SCORE: float = 0.95
    MIN_IMPROVEMENT_THRESHOLD: float = 0.05
    IMPROVEMENT_WINDOW: int = 3
    PATIENCE_ITERATIONS: int = 2
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    API_AUTH_TOKEN: str = ""
    RATE_LIMIT_REQUESTS: int = 10
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]

    class Config:
        env_file = ".env"

settings = Settings()
