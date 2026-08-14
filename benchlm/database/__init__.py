"""Database package for BenchLM."""

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
from benchlm.database.repository import (
    DatabaseRepository,
    get_repository,
    init_database,
    close_database,
)
from benchlm.database.migrations import (
    init_migrations,
    create_migration,
    upgrade_database,
    downgrade_database,
    get_current_revision,
    get_migration_history,
)

__all__ = [
    # Models
    "Model",
    "BenchmarkRun",
    "Prompt",
    "TokenEvent",
    "HardwareSample",
    "QualityScore",
    "StatisticalSummary",
    "ComparisonSet",
    "ProviderType",
    "BenchmarkStatus",
    "ModelQuantization",
    # Repository
    "DatabaseRepository",
    "get_repository",
    "init_database",
    "close_database",
    # Migrations
    "init_migrations",
    "create_migration",
    "upgrade_database",
    "downgrade_database",
    "get_current_revision",
    "get_migration_history",
]