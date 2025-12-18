from sqlalchemy import text
from sqlalchemy.orm import Session


def ensure_column_exists(
    db: Session,
    table: str,
    column: str,
    column_sql: str,
):
    """
    SQLite-safe column check + add.

    Example:
      ensure_column_exists(
          db,
          "users",
          "favourite_rotas",
          "TEXT"
      )
    """
    result = db.execute(
        text(f"PRAGMA table_info({table})")
    ).fetchall()

    existing_columns = {row[1] for row in result}

    if column not in existing_columns:
        db.execute(
            text(f"ALTER TABLE {table} ADD COLUMN {column} {column_sql}")
        )
        db.commit()
