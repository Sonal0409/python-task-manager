"""SQLite persistence helpers for tasks."""

import sqlite3
import uuid
from pathlib import Path


DEFAULT_DATABASE_PATH = Path(__file__).with_name("tasks.db")


def connect(database_path: str | Path = DEFAULT_DATABASE_PATH) -> sqlite3.Connection:
    path = str(database_path)
    connection = sqlite3.connect(path, uri=path.startswith("file:"))
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> tuple[str | Path, sqlite3.Connection | None]:
    anchor = None
    if str(database_path) == ":memory:":
        path = f"file:task-manager-{uuid.uuid4().hex}?mode=memory&cache=shared"
        anchor = connect(path)
        connection = anchor
    else:
        path = database_path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        connection = connect(path)
    try:
        with connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'todo'
                        CHECK (status IN ('todo', 'in_progress', 'done')),
                    created_at TEXT NOT NULL
                )
                """
            )
    finally:
        if anchor is None:
            connection.close()
    return path, anchor


def list_tasks(database_path: str | Path) -> list[sqlite3.Row]:
    with connect(database_path) as connection:
        return connection.execute(
            "SELECT id, title, description, status, created_at "
            "FROM tasks ORDER BY id DESC"
        ).fetchall()


def create_task(
    database_path: str | Path,
    title: str,
    description: str,
    status: str,
    created_at: str,
) -> sqlite3.Row:
    with connect(database_path) as connection:
        cursor = connection.execute(
            "INSERT INTO tasks (title, description, status, created_at) "
            "VALUES (?, ?, ?, ?)",
            (title, description, status, created_at),
        )
        row = connection.execute(
            "SELECT id, title, description, status, created_at FROM tasks WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    return row


def update_task(
    database_path: str | Path, task_id: int, values: dict[str, str]
) -> sqlite3.Row | None:
    columns = ", ".join(f"{column} = ?" for column in values)
    with connect(database_path) as connection:
        cursor = connection.execute(
            f"UPDATE tasks SET {columns} WHERE id = ?",
            (*values.values(), task_id),
        )
        if cursor.rowcount == 0:
            return None
        return connection.execute(
            "SELECT id, title, description, status, created_at FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()


def delete_task(database_path: str | Path, task_id: int) -> bool:
    with connect(database_path) as connection:
        cursor = connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        return cursor.rowcount > 0
