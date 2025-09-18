# db/migrations/env.py

from logging.config import fileConfig
from sqlalchemy import create_engine, pool 
from alembic import context
from datetime import timezone 
from core.config import settings
from models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
sync_url = settings.DATABASE_URL.replace("aiomysql", "pymysql")

# offline migration
def run_migrations_offline() -> None:
    url = settings.DATABASE_URL 
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()

# online migration
def run_migrations_online() -> None:
    connectable = create_engine( 
        sync_url,
        poolclass=pool.NullPool,
        future=True,
    )

    with connectable.connect() as connection:
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
    run_migrations_online()