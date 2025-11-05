import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from dotenv import load_dotenv

from alembic import context

# Load environment variables
load_dotenv()

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Disable interpolation in ConfigParser to avoid issues with % characters in URLs
if hasattr(config, "file_config") and config.file_config is not None:
    # Disable interpolation to handle % characters in database URLs
    config.file_config._interpolation = None

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import your models here for autogenerate support
from app.models import Base
target_metadata = Base.metadata

# Get database URL from environment variable (if available)
# Otherwise, use the URL from alembic.ini
DATABASE_URL = os.getenv("DATABASE_URL")

# If no env variable, read URL directly from file_config to avoid interpolation issues
if not DATABASE_URL and hasattr(config, "file_config") and config.file_config is not None:
    try:
        # Read directly from file_config without interpolation
        alembic_section = config.config_ini_section
        if config.file_config.has_section(alembic_section):
            if config.file_config.has_option(alembic_section, "sqlalchemy.url"):
                # Get raw value without interpolation
                DATABASE_URL = config.file_config.get(alembic_section, "sqlalchemy.url", raw=True)
    except Exception:
        # Fallback to default method if reading fails
        pass


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Get database URL - should be set above from env or file_config
    url = DATABASE_URL
    if not url:
        # Last resort fallback
        try:
            url = config.get_main_option("sqlalchemy.url")
        except Exception:
            raise RuntimeError("Could not determine database URL. Please set DATABASE_URL environment variable or configure sqlalchemy.url in alembic.ini")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Get database URL - should be set above from env or file_config
    db_url = DATABASE_URL
    if not db_url:
        # Last resort fallback
        try:
            db_url = config.get_main_option("sqlalchemy.url")
        except Exception:
            raise RuntimeError("Could not determine database URL. Please set DATABASE_URL environment variable or configure sqlalchemy.url in alembic.ini")
    
    # Build configuration dict manually to avoid ConfigParser interpolation issues
    configuration = {
        "sqlalchemy.url": db_url
    }
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
