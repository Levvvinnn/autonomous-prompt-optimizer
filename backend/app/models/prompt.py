from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from datetime import datetime
from app.database import Base

class OptimizationSession(Base):
    __tablename__ = "optimization_sessions"

    id = Column(Integer, primary_key=True)
    task_type = Column(String)
    initial_prompt = Column(Text)
    final_prompt = Column(Text)
    final_score = Column(Float)
    total_iterations = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer)
    iteration = Column(Integer)
    prompt_text = Column(Text)
    output_text = Column(Text)
    score = Column(Float)
    failure_analysis = Column(Text)
    correctness = Column(Float)
    clarity = Column(Float)
    completeness = Column(Float)
    conciseness = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)