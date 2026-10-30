"""Benchmark models for driver-benchmark-api feature."""

from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Enum as SQLEnum
from sqlalchemy.orm import declarative_base

from app.services.database import Base


class BenchmarkStatus(str, Enum):
    """Benchmark run status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BenchmarkRun(Base):
    """Benchmark run model for latency measurements."""

    __tablename__ = "benchmark_runs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    driver = Column(String(100), nullable=False)  # e.g., "lume", "qemu", "firecracker"
    status = Column(SQLEnum(BenchmarkStatus), default=BenchmarkStatus.PENDING, nullable=False, index=True)

    # Configuration (from issue #3971)
    observation_timeout_ms = Column(Integer, default=1000, nullable=False)
    settle_timeout_ms = Column(Integer, default=800, nullable=False)
    poll_interval_ms = Column(Integer, default=50, nullable=False)

    # Results
    iterations = Column(Integer, default=0, nullable=False)
    min_latency_ms = Column(Float, nullable=True)
    max_latency_ms = Column(Float, nullable=True)
    avg_latency_ms = Column(Float, nullable=True)
    p50_latency_ms = Column(Float, nullable=True)
    p95_latency_ms = Column(Float, nullable=True)
    p99_latency_ms = Column(Float, nullable=True)

    # Error info
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


class BenchmarkIteration(Base):
    """Individual benchmark iteration for detailed latency tracking."""

    __tablename__ = "benchmark_iterations"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, nullable=False, index=True)
    iteration = Column(Integer, nullable=False)
    latency_ms = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

