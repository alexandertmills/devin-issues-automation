from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class GitHubIssue(Base):
    __tablename__ = "github_issues"
    
    id = Column(Integer, primary_key=True, index=True)
    github_issue_id = Column(BigInteger, unique=True, index=True)
    title = Column(String, index=True)
    body = Column(Text)
    state = Column(String)
    repository = Column(String)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
class DevinSession(Base):
    __tablename__ = "devin_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    github_issue_id = Column(BigInteger, index=True)
    session_id = Column(String, unique=True, index=True)
    session_type = Column(String)  # "scope" or "execute"
    status = Column(String)  # "pending", "running", "completed", "failed"
    confidence_score = Column(Float, nullable=True)
    action_plan = Column(Text, nullable=True)
    result = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
