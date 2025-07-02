from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float, BigInteger, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
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
    html_url = Column(String)
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
                DevinSession.github_issue == self.id,
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

class GitHubUser(Base):
    __tablename__ = "github_users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    installation_id = Column(String, nullable=True)
    access_token = Column(String, nullable=True)
    token_expiry = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    repositories = relationship("Repository", back_populates="github_user")

class Repository(Base):
    __tablename__ = "repositories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    github_user = Column(Integer, ForeignKey("github_users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    github_user_rel = relationship("GitHubUser", back_populates="repositories")
    
    def get_owner_username(self):
        return self.github_user_rel.username if self.github_user_rel else None
    
    def get_issues_api_url(self):
        owner_username = self.get_owner_username()
        if owner_username:
            return f"https://api.github.com/repos/{owner_username}/{self.name}/issues"
        return None
class DevinSession(Base):
    __tablename__ = "devin_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    github_issue = Column(Integer, ForeignKey('github_issues.id'), index=True)
    session_id = Column(String, unique=True, index=True)
    session_type = Column(String)  # "scope" or "execute"
    status = Column(String)  # "pending", "running", "completed", "failed"
    confidence_score = Column(Float, nullable=True)
    action_plan = Column(Text, nullable=True)
    result = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
