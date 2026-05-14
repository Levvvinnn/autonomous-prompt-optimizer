from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from datetime import datetime
from app.database import Base

class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id = Column(Integer, primary_key=True)
    task_type = Column(String)
    prompt_text = Column(Text)
    iteration = Column(Integer)
    score = Column(Float)
    failure_analysis = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)