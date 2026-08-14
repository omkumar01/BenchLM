"""Database migrations for BenchLM using Alembic."""

import os
from pathlib import Path
from typing import Optional

from alembic import command
from alembic.config import Config as AlembicConfig

from benchlm.config import get_config, DatabaseConfig


def get_alembic_config(config: DatabaseConfig | None = None) -> AlembicConfig:
    """Get Alembic configuration."""
    if config is None:
        config = get_config().database

    # Get the directory containing this file
    migrations_dir = Path(__file__).parent / "alembic"

    alembic_cfg = AlembicConfig()
    alembic_cfg.set_main_option("script_location", str(migrations_dir))
    alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite+aiosqlite:///{config.path}")
    alembic_cfg.set_main_option("file_template", "%(year)d_%(month).2d_%(day).2d_%(hour).2d%(minute).2d_%(slug)s")

    return alembic_cfg


def init_migrations(config: DatabaseConfig | None = None) -> None:
    """Initialize Alembic migration environment."""
    if config is None:
        config = get_config().database

    migrations_dir = Path(__file__).parent / "alembic"
    migrations_dir.mkdir(exist_ok=True)

    # Create alembic.ini if it doesn't exist
    alembic_ini = migrations_dir / "alembic.ini"
    if not alembic_ini.exists():
        alembic_cfg = get_alembic_config(config)
        # Write default alembic.ini
        with open(alembic_ini, "w") as f:
            alembic_cfg.file_config.write(f)

    # Create env.py if it doesn't exist
    env_py = migrations_dir / "env.py"
    if not env_py.exists():
        env_content = '''"""Alembic environment configuration for BenchLM."""

import sys
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from benchlm.database.models import SQLModel
from benchlm.config import get_config

config = context.config

# Override sqlalchemy.url from config
db_config = get_config().database
config.set_main_option("sqlalchemy.url", f"sqlite+aiosqlite:///{db_config.path}")

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = create_async_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    import asyncio
    asyncio.run(run_migrations_online())
'''
        env_py.write_text(env_content)

    # Create script.py.mako template
    script_mako = migrations_dir / "script.py.mako"
    if not script_mako.exists():
        script_content = '''"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
'''
        script_mako.write_text(script_content)


def create_migration(message: str, config: DatabaseConfig | None = None) -> str:
    """Create a new migration revision."""
    alembic_cfg = get_alembic_config(config)
    init_migrations(config)

    # Generate revision
    command.revision(alembic_cfg, message=message, autogenerate=True)

    # Get the latest revision file
    migrations_dir = Path(__file__).parent / "alembic" / "versions"
    if migrations_dir.exists():
        revisions = sorted(migrations_dir.glob("*.py"))
        if revisions:
            return str(revisions[-1])

    return ""


def upgrade_database(revision: str = "head", config: DatabaseConfig | None = None) -> None:
    """Upgrade database to a specific revision."""
    alembic_cfg = get_alembic_config(config)
    command.upgrade(alembic_cfg, revision)


def downgrade_database(revision: str = "-1", config: DatabaseConfig | None = None) -> None:
    """Downgrade database by one revision."""
    alembic_cfg = get_alembic_config(config)
    command.downgrade(alembic_cfg, revision)


def get_current_revision(config: DatabaseConfig | None = None) -> Optional[str]:
    """Get current database revision."""
    from alembic.script import ScriptDirectory
    from alembic.runtime.migration import MigrationContext
    from sqlalchemy import create_engine

    if config is None:
        config = get_config().database

    engine = create_engine(f"sqlite:///{config.path}")
    with engine.connect() as conn:
        context = MigrationContext.configure(conn)
        return context.get_current_revision()


def get_migration_history(config: DatabaseConfig | None = None) -> list[dict]:
    """Get migration history."""
    from alembic.script import ScriptDirectory

    alembic_cfg = get_alembic_config(config)
    script_dir = ScriptDirectory.from_config(alembic_cfg)

    history = []
    for rev in script_dir.walk_revisions():
        history.append({
            "revision": rev.revision,
            "down_revision": rev.down_revision,
            "message": rev.message,
            "create_date": str(rev.create_date) if rev.create_date else None,
        })
    return history