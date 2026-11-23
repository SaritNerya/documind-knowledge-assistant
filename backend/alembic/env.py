from logging.config import fileConfig

from alembic import context

from app.core.database import Base, engine
from app.models import chunk, conversation, document, message, question_usage, user  # noqa: F401 רישום הטבלאות

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# מאפשר בעתיד: alembic revision --autogenerate
target_metadata = Base.metadata


def run_migrations_online() -> None:
    # כל ההגירות רצות בטרנזקציה אחת: כישלון באמצע לא משאיר מסד במצב חלקי
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            transaction_per_migration=False,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    raise SystemExit("Offline mode is not supported. Run against a live database.")
run_migrations_online()
