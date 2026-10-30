"""Benchmark service for driver-benchmark-api feature."""

import asyncio
import random
import time
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.benchmark import BenchmarkRun, BenchmarkIteration, BenchmarkStatus
from app.core.config import get_settings


class BenchmarkService:
    """Service for managing benchmark runs."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()

    async def create_benchmark(
        self,
        name: str,
        driver: str,
        observation_timeout_ms: Optional[int] = None,
        settle_timeout_ms: Optional[int] = None,
        poll_interval_ms: Optional[int] = None,
    ) -> BenchmarkRun:
        """Create a new benchmark run."""
        run = BenchmarkRun(
            name=name,
            driver=driver,
            status=BenchmarkStatus.PENDING,
            observation_timeout_ms=observation_timeout_ms or self.settings.benchmark_observation_timeout_ms,
            settle_timeout_ms=settle_timeout_ms or self.settings.benchmark_settle_timeout_ms,
            poll_interval_ms=poll_interval_ms or self.settings.benchmark_poll_interval_ms,
        )
        self.db.add(run)
        await self.db.flush()
        await self.db.refresh(run)
        return run

    async def get_benchmark(self, benchmark_id: int) -> Optional[BenchmarkRun]:
        """Get a benchmark run by ID."""
        result = await self.db.execute(
            select(BenchmarkRun).where(BenchmarkRun.id == benchmark_id)
        )
        return result.scalar_one_or_none()

    async def list_benchmarks(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[BenchmarkStatus] = None,
        driver: Optional[str] = None,
    ) -> tuple[List[BenchmarkRun], int]:
        """List benchmark runs with pagination and filtering."""
        query = select(BenchmarkRun)
        count_query = select(func.count(BenchmarkRun.id))

        if status:
            query = query.where(BenchmarkRun.status == status)
            count_query = count_query.where(BenchmarkRun.status == status)
        if driver:
            query = query.where(BenchmarkRun.driver == driver)
            count_query = count_query.where(BenchmarkRun.driver == driver)

        query = query.order_by(BenchmarkRun.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        items = result.scalars().all()

        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        return list(items), total

    async def run_benchmark(self, benchmark_id: int) -> BenchmarkRun:
        """Run a benchmark (simulated for now)."""
        run = await self.get_benchmark(benchmark_id)
        if not run:
            raise ValueError(f"Benchmark {benchmark_id} not found")

        if run.status != BenchmarkStatus.PENDING:
            raise ValueError(f"Benchmark {benchmark_id} is not in pending state")

        run.status = BenchmarkStatus.RUNNING
        run.started_at = datetime.utcnow()
        await self.db.flush()

        # Simulate benchmark iterations
        # In a real implementation, this would call the actual driver
        num_iterations = 100
        latencies = []

        for i in range(num_iterations):
            # Simulate latency measurement
            # In reality, this would call the driver and measure response time
            await asyncio.sleep(run.poll_interval_ms / 1000.0)

            # Generate realistic latency based on driver type
            base_latency = self._get_base_latency(run.driver)
            noise = random.uniform(-0.1, 0.1) * base_latency
            latency = base_latency + noise
            latencies.append(latency)

            iteration = BenchmarkIteration(
                run_id=run.id,
                iteration=i,
                latency_ms=latency,
            )
            self.db.add(iteration)

            # Check for cancellation (in real impl, check a cancellation token)
            # For now, we just run to completion

        # Calculate statistics
        latencies.sort()
        run.iterations = num_iterations
        run.min_latency_ms = latencies[0]
        run.max_latency_ms = latencies[-1]
        run.avg_latency_ms = sum(latencies) / len(latencies)
        run.p50_latency_ms = latencies[len(latencies) // 2]
        run.p95_latency_ms = latencies[int(len(latencies) * 0.95)]
        run.p99_latency_ms = latencies[int(len(latencies) * 0.99)]

        run.status = BenchmarkStatus.COMPLETED
        run.completed_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(run)

        return run

    def _get_base_latency(self, driver: str) -> float:
        """Get base latency for a driver type (simulated)."""
        base_latencies = {
            "lume": 5.0,
            "qemu": 15.0,
            "firecracker": 3.0,
            "docker": 2.0,
        }
        return base_latencies.get(driver.lower(), 10.0)

    async def cancel_benchmark(self, benchmark_id: int) -> BenchmarkRun:
        """Cancel a running benchmark."""
        run = await self.get_benchmark(benchmark_id)
        if not run:
            raise ValueError(f"Benchmark {benchmark_id} not found")

        if run.status not in (BenchmarkStatus.PENDING, BenchmarkStatus.RUNNING):
            raise ValueError(f"Cannot cancel benchmark in {run.status} state")

        run.status = BenchmarkStatus.CANCELLED
        run.completed_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(run)
        return run

