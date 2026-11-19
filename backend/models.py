"""Task model and request-data validation."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


VALID_STATUSES = {"todo", "in_progress", "done"}
MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 2000


@dataclass(frozen=True)
class Task:
    id: int
    title: str
    description: str
    status: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at,
        }

    @classmethod
    def from_row(cls, row: Any) -> "Task":
        return cls(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            status=row["status"],
            created_at=row["created_at"],
        )


def validate_task_input(
    payload: Any, *, creating: bool
) -> tuple[dict[str, str] | None, dict[str, str]]:
    """Return normalized fields and field-specific validation errors."""
    if not isinstance(payload, dict):
        return None, {"body": "Request body must be a JSON object."}

    allowed_fields = {"title", "description"} if creating else {
        "title",
        "description",
        "status",
    }
    unknown_fields = set(payload) - allowed_fields
    if unknown_fields:
        return None, {"body": f"Unknown field(s): {', '.join(sorted(unknown_fields))}."}
    if not creating and not payload:
        return None, {"body": "Provide at least one field to update."}

    values: dict[str, str] = {}
    errors: dict[str, str] = {}

    if creating and "title" not in payload:
        errors["title"] = "Title is required."
    if "title" in payload:
        title = payload["title"]
        if not isinstance(title, str) or not title.strip():
            errors["title"] = "Title must be a non-empty string."
        elif len(title.strip()) >= MAX_TITLE_LENGTH:
            errors["title"] = f"Title must be {MAX_TITLE_LENGTH} characters or fewer."
        else:
            values["title"] = title.strip()

    if "description" in payload:
        description = payload["description"]
        if not isinstance(description, str):
            errors["description"] = "Description must be a string."
        elif len(description) > MAX_DESCRIPTION_LENGTH:
            errors["description"] = (
                f"Description must be {MAX_DESCRIPTION_LENGTH} characters or fewer."
            )
        else:
            values["description"] = description.strip()

    if "status" in payload:
        status = payload["status"]
        if not isinstance(status, str) or status not in VALID_STATUSES:
            errors["status"] = (
                "Status must be one of: todo, in_progress, done."
            )
        else:
            values["status"] = status

    return (None, errors) if errors else (values, {})


def current_timestamp() -> str:
    """Return a timezone-aware UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
