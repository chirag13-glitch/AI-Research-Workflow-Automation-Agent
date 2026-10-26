"""SQLAlchemy ORM models for Users, API keys, Tasks, Steps, Sources, and Evaluations."""
from datetime import datetime
import json
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    """User account entity."""
    __tablename__ = "users"

    id = Column(String(64), primary_key=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(128), unique=True, nullable=False, index=True)
    is_admin = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    api_keys = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")


class ApiKey(Base):
    """API key entity associated with a user."""
    __tablename__ = "api_keys"

    id = Column(String(64), primary_key=True)
    key_hash = Column(String(128), unique=True, nullable=False, index=True)
    prefix = Column(String(16), nullable=False)  # First few chars for display
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(64), default="default")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="api_keys")


class Task(Base):
    """Research task persistent record."""
    __tablename__ = "tasks"

    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    topic = Column(String(512), nullable=False)
    status = Column(String(32), default="CREATED", nullable=False, index=True)
    constraints_json = Column(Text, default="[]", nullable=False)
    plan_json = Column(Text, nullable=True)
    report_markdown = Column(Text, nullable=True)
    max_tool_calls = Column(Integer, default=15, nullable=False)
    current_tool_calls = Column(Integer, default=0, nullable=False)
    requires_approval = Column(Boolean, default=False, nullable=False)
    approval_reason = Column(String(512), nullable=True)
    approval_status = Column(String(32), nullable=True)  # PENDING, APPROVED, REJECTED
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="tasks")
    step_logs = relationship("StepLog", back_populates="task", cascade="all, delete-orphan")
    sources = relationship("Source", back_populates="task", cascade="all, delete-orphan")

    def get_constraints(self) -> List[str]:
        try:
            return json.loads(self.constraints_json or "[]")
        except Exception:
            return []

    def set_constraints(self, constraints: List[str]) -> None:
        self.constraints_json = json.dumps(constraints)


class StepLog(Base):
    """Audit log entry for a node/tool step within a task."""
    __tablename__ = "step_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(64), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    step_index = Column(Integer, default=0, nullable=False)
    node_name = Column(String(64), nullable=False)
    status = Column(String(32), default="RUNNING", nullable=False)
    log_message = Column(String(512), nullable=False)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    task = relationship("Task", back_populates="step_logs")


class Source(Base):
    """Verified external source retrieved during task execution."""
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(64), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    source_id = Column(String(32), nullable=False)  # e.g. src-1
    url = Column(String(1024), nullable=False)
    title = Column(String(512), nullable=False)
    domain = Column(String(256), nullable=False)
    retrieved_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    raw_excerpt = Column(Text, nullable=True)

    task = relationship("Task", back_populates="sources")


class EvaluationRun(Base):
    """Benchmark evaluation experiment record."""
    __tablename__ = "evaluation_runs"

    id = Column(String(64), primary_key=True)
    run_name = Column(String(128), nullable=False)
    model_name = Column(String(64), nullable=False)
    dataset_name = Column(String(64), nullable=False)
    total_cases = Column(Integer, default=0, nullable=False)
    passed_cases = Column(Integer, default=0, nullable=False)
    avg_grounding_score = Column(Float, default=0.0, nullable=False)
    avg_latency_ms = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    cases = relationship("EvaluationCase", back_populates="run", cascade="all, delete-orphan")


class EvaluationCase(Base):
    """Individual test case result within an EvaluationRun."""
    __tablename__ = "evaluation_cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    case_id = Column(String(64), nullable=False)
    topic = Column(String(512), nullable=False)
    category = Column(String(64), nullable=False)
    passed = Column(Boolean, default=False, nullable=False)
    score = Column(Float, default=0.0, nullable=False)
    metrics_json = Column(Text, default="{}", nullable=False)
    error_message = Column(Text, nullable=True)

    run = relationship("EvaluationRun", back_populates="cases")
