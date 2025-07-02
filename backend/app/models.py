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
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
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
    github_user_id = Column(Integer, ForeignKey("github_users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    github_user = relationship("GitHubUser", back_populates="repositories")
    
    def get_owner_username(self):
        return self.github_user.username if self.github_user else None
    
    def get_issues_api_url(self):
        owner_username = self.get_owner_username()
        if owner_username:
            return f"https://api.github.com/repos/{owner_username}/{self.name}/issues"
        return None

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
