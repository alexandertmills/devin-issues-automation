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
    
    async def get_state(self, db_session) -> str:
        """
        Assess the state of this issue based on associated devin sessions:
        - ready-to-scope: no devin_session associated with this issue OR issue modified after most recent session
        - scope-in-progress: devin_session exists but no confidence_score
        - scope-complete: devin_session exists with confidence_score
        """
        from sqlalchemy import select
        
        result = await db_session.execute(
            select(DevinSession).where(
                DevinSession.github_issue_id == self.github_issue_id,
                DevinSession.session_type == "scope"
            ).order_by(DevinSession.created_at.desc())
        )
        most_recent_scope_session = result.scalar_one_or_none()
        
        if not most_recent_scope_session:
            return "ready-to-scope"
        
        if self.updated_at > most_recent_scope_session.created_at:
            return "ready-to-scope"
        
        if most_recent_scope_session.confidence_score is None:
            return "scope-in-progress"
        else:
            return "scope-complete"
    
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
