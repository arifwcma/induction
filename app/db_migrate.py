from sqlalchemy import text


COLUMN_MIGRATIONS = [
    "ALTER TABLE clause ADD COLUMN IF NOT EXISTS category VARCHAR(50) DEFAULT '' NOT NULL",
    "ALTER TABLE trainer_kb_entry ALTER COLUMN trainer_id DROP NOT NULL",
]


async def apply_column_migrations(connection):
    for statement in COLUMN_MIGRATIONS:
        await connection.execute(text(statement))
