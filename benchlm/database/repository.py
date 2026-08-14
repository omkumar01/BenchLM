"""Database repository for BenchLM using SQLModel."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlmodel import SQLModel

from benchlm.config import get_config, DatabaseConfig
from benchlm.database.models import (
    Model,
    BenchmarkRun,
    Prompt,
    TokenEvent,
    HardwareSample,
    QualityScore,
    StatisticalSummary,
    ComparisonSet,
    ProviderType,
    BenchmarkStatus,
    ModelQuantization,
)


class DatabaseRepository:
    """Repository for database operations."""

    def __init__(self, config: DatabaseConfig | None = None):
        self.config = config or get_config().database
        self._engine = None
        self._session_factory = None

    @property
    def engine(self):
        if self._engine is None:
            db_path = self.config.path
            # Ensure directory exists
            import os
            os.makedirs(os.path.dirname(db_path), exist_ok=True)

            self._engine = create_async_engine(
                f"sqlite+aiosqlite:///{db_path}",
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                echo=self.config.echo,
            )
        return self._engine

    @property
    def session_factory(self):
        if self._session_factory is None:
            self._session_factory = async_sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )
        return self._session_factory

    @asynccontextmanager
    async def session(self) -> AsyncSession:
        """Get a database session."""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def init_db(self) -> None:
        """Initialize database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    async def close(self) -> None:
        """Close database connections."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None

    # Model operations
    async def create_model(self, model: Model) -> Model:
        async with self.session() as session:
            session.add(model)
            await session.flush()
            await session.refresh(model)
            return model

    async def get_model(self, model_id: int) -> Optional[Model]:
        async with self.session() as session:
            return await session.get(Model, model_id)

    async def get_model_by_uuid(self, uuid: str) -> Optional[Model]:
        async with self.session() as session:
            stmt = select(Model).where(Model.uuid == uuid)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def list_models(
        self,
        provider: Optional[ProviderType] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Model]:
        async with self.session() as session:
            stmt = select(Model).order_by(Model.created_at.desc())
            if provider:
                stmt = stmt.where(Model.provider == provider)
            stmt = stmt.limit(limit).offset(offset)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def update_model(self, model: Model) -> Model:
        async with self.session() as session:
            model.updated_at = datetime.utcnow()
            session.add(model)
            await session.flush()
            await session.refresh(model)
            return model

    async def delete_model(self, model_id: int) -> bool:
        async with self.session() as session:
            model = await session.get(Model, model_id)
            if model:
                await session.delete(model)
                return True
            return False

    # BenchmarkRun operations
    async def create_benchmark_run(self, run: BenchmarkRun) -> BenchmarkRun:
        async with self.session() as session:
            session.add(run)
            await session.flush()
            await session.refresh(run)
            return run

    async def get_benchmark_run(self, run_id: int) -> Optional[BenchmarkRun]:
        async with self.session() as session:
            return await session.get(BenchmarkRun, run_id)

    async def get_benchmark_run_by_uuid(self, uuid: str) -> Optional[BenchmarkRun]:
        async with self.session() as session:
            stmt = select(BenchmarkRun).where(BenchmarkRun.uuid == uuid)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def list_benchmark_runs(
        self,
        model_id: Optional[int] = None,
        status: Optional[BenchmarkStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[BenchmarkRun]:
        async with self.session() as session:
            stmt = select(BenchmarkRun).order_by(BenchmarkRun.created_at.desc())
            if model_id:
                stmt = stmt.where(BenchmarkRun.model_id == model_id)
            if status:
                stmt = stmt.where(BenchmarkRun.status == status)
            stmt = stmt.limit(limit).offset(offset)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def update_benchmark_run(self, run: BenchmarkRun) -> BenchmarkRun:
        async with self.session() as session:
            run.updated_at = datetime.utcnow()
            session.add(run)
            await session.flush()
            await session.refresh(run)
            return run

    async def update_run_status(
        self, run_id: int, status: BenchmarkStatus, error: Optional[str] = None
    ) -> bool:
        async with self.session() as session:
            run = await session.get(BenchmarkRun, run_id)
            if not run:
                return False
            run.status = status
            if error:
                run.error_message = error
            if status == BenchmarkStatus.RUNNING and not run.started_at:
                run.started_at = datetime.utcnow()
            elif status in (BenchmarkStatus.COMPLETED, BenchmarkStatus.FAILED, BenchmarkStatus.CANCELLED):
                run.completed_at = datetime.utcnow()
                if run.started_at:
                    run.duration_seconds = (run.completed_at - run.started_at).total_seconds()
            await session.flush()
            return True

    # Prompt operations
    async def create_prompts(self, prompts: list[Prompt]) -> list[Prompt]:
        async with self.session() as session:
            session.add_all(prompts)
            await session.flush()
            for p in prompts:
                await session.refresh(p)
            return prompts

    async def get_prompts_for_run(self, run_id: int) -> list[Prompt]:
        async with self.session() as session:
            stmt = select(Prompt).where(Prompt.benchmark_run_id == run_id)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    # TokenEvent operations (batched for performance)
    async def create_token_events(self, events: list[TokenEvent]) -> list[TokenEvent]:
        async with self.session() as session:
            session.add_all(events)
            await session.flush()
            return events

    async def get_token_events(
        self, run_id: int, prompt_id: Optional[int] = None, limit: int = 10000
    ) -> list[TokenEvent]:
        async with self.session() as session:
            stmt = select(TokenEvent).where(TokenEvent.benchmark_run_id == run_id)
            if prompt_id:
                stmt = stmt.where(TokenEvent.prompt_id == prompt_id)
            stmt = stmt.order_by(TokenEvent.timestamp_us).limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    # HardwareSample operations (batched)
    async def create_hardware_samples(self, samples: list[HardwareSample]) -> list[HardwareSample]:
        async with self.session() as session:
            session.add_all(samples)
            await session.flush()
            return samples

    async def get_hardware_samples(
        self, run_id: int, limit: int = 10000
    ) -> list[HardwareSample]:
        async with self.session() as session:
            stmt = (
                select(HardwareSample)
                .where(HardwareSample.benchmark_run_id == run_id)
                .order_by(HardwareSample.timestamp_us)
                .limit(limit)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_latest_hardware_sample(self, run_id: int) -> Optional[HardwareSample]:
        async with self.session() as session:
            stmt = (
                select(HardwareSample)
                .where(HardwareSample.benchmark_run_id == run_id)
                .order_by(HardwareSample.timestamp_us.desc())
                .limit(1)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    # QualityScore operations
    async def create_quality_scores(self, scores: list[QualityScore]) -> list[QualityScore]:
        async with self.session() as session:
            session.add_all(scores)
            await session.flush()
            return scores

    async def get_quality_scores(self, run_id: int) -> list[QualityScore]:
        async with self.session() as session:
            stmt = select(QualityScore).where(QualityScore.benchmark_run_id == run_id)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    # StatisticalSummary operations
    async def create_statistical_summary(self, summary: StatisticalSummary) -> StatisticalSummary:
        async with self.session() as session:
            session.add(summary)
            await session.flush()
            await session.refresh(summary)
            return summary

    async def get_statistical_summary(self, run_id: int) -> Optional[StatisticalSummary]:
        async with self.session() as session:
            stmt = select(StatisticalSummary).where(
                StatisticalSummary.benchmark_run_id == run_id
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def update_statistical_summary(self, summary: StatisticalSummary) -> StatisticalSummary:
        async with self.session() as session:
            summary.computed_at = datetime.utcnow()
            session.add(summary)
            await session.flush()
            await session.refresh(summary)
            return summary

    # ComparisonSet operations
    async def create_comparison_set(self, comp_set: ComparisonSet) -> ComparisonSet:
        async with self.session() as session:
            session.add(comp_set)
            await session.flush()
            await session.refresh(comp_set)
            return comp_set

    async def get_comparison_set(self, set_id: int) -> Optional[ComparisonSet]:
        async with self.session() as session:
            return await session.get(ComparisonSet, set_id)

    async def list_comparison_sets(self, limit: int = 100) -> list[ComparisonSet]:
        async with self.session() as session:
            stmt = select(ComparisonSet).order_by(ComparisonSet.updated_at.desc()).limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def update_comparison_set(self, comp_set: ComparisonSet) -> ComparisonSet:
        async with self.session() as session:
            comp_set.updated_at = datetime.utcnow()
            session.add(comp_set)
            await session.flush()
            await session.refresh(comp_set)
            return comp_set

    async def delete_comparison_set(self, set_id: int) -> bool:
        async with self.session() as session:
            comp_set = await session.get(ComparisonSet, set_id)
            if comp_set:
                await session.delete(comp_set)
                return True
            return False

    # Aggregate queries for dashboard
    async def get_run_count(self) -> int:
        async with self.session() as session:
            stmt = select(func.count(BenchmarkRun.id))
            result = await session.execute(stmt)
            return result.scalar() or 0

    async def get_model_count(self) -> int:
        async with self.session() as session:
            stmt = select(func.count(Model.id))
            result = await session.execute(stmt)
            return result.scalar() or 0

    async def get_latest_runs(self, limit: int = 10) -> list[BenchmarkRun]:
        return await self.list_benchmark_runs(limit=limit)

    async def get_best_runs_by_score(self, limit: int = 10) -> list[BenchmarkRun]:
        async with self.session() as session:
            stmt = (
                select(BenchmarkRun)
                .where(BenchmarkRun.overall_score.is_not(None))
                .order_by(BenchmarkRun.overall_score.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())


# Singleton instance
_repository: DatabaseRepository | None = None


def get_repository() -> DatabaseRepository:
    """Get the global database repository."""
    global _repository
    if _repository is None:
        _repository = DatabaseRepository()
    return _repository


async def init_database() -> DatabaseRepository:
    """Initialize database and return repository."""
    repo = get_repository()
    await repo.init_db()
    return repo


async def close_database() -> None:
    """Close database connections."""
    global _repository
    if _repository:
        await _repository.close()
        _repository = None