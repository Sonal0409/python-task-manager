# Taskflow — Task Management Web Application

A lightweight task-management dashboard built with a vanilla HTML/CSS/JavaScript frontend, a Python Flask REST API, and SQLite persistence. Create tasks, review them in a responsive dashboard, change their status, and delete them.

## Architecture

```text
frontend/       Static responsive dashboard (HTML, CSS, vanilla JavaScript)
backend/        Flask API, SQLite persistence helpers, and task validation/model
tests/          Pytest API tests using isolated SQLite databases
```

The API listens on `http://127.0.0.1:5000`. The frontend calls the API at that address and is served separately on port `5500`. SQLite creates `backend/tasks.db` on first backend startup. Set `TASK_MANAGER_DATABASE` to use a different database path.

## Requirements

- Python 3.10 or later
- pip
- A modern web browser

## Installation

Run these commands from the project root:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

If PowerShell prevents environment activation, either allow activation for the current terminal or invoke the environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Start the backend

From the project root, activate the virtual environment and run:

```powershell
py -m backend.app
```

The API is available at `http://127.0.0.1:5000`. Keep this terminal open while using the app. To select a different SQLite file, set the environment variable before starting the server:

```powershell
$env:TASK_MANAGER_DATABASE = "C:\path\to\tasks.db"
py -m backend.app
```

## Launch the frontend

In a second terminal, from the project root, run:

```powershell
py -m http.server 5500 --directory frontend
```

Open [http://127.0.0.1:5500](http://127.0.0.1:5500) in your browser. The frontend needs the backend running; if its initial task request fails, start the backend and refresh the page.

## REST API

All request and response bodies use JSON. Task statuses are `todo`, `in_progress`, and `done`. Validation errors return `400` with an `error` and field-specific `details`; missing task IDs return `404`.

| Method | Endpoint | Description | Success |
| --- | --- | --- | --- |
| `GET` | `/api/tasks` | List tasks, newest first | `200` with `{ "tasks": [...] }` |
| `POST` | `/api/tasks` | Create a task using required `title` and optional `description` | `201` with `{ "task": {...} }` |
| `PUT` | `/api/tasks/<id>` | Update one or more of `title`, `description`, and `status` | `200` with `{ "task": {...} }` |
| `DELETE` | `/api/tasks/<id>` | Delete a task | `200` with a confirmation message |

Example create request:

```json
{
  "title": "Prepare weekly update",
  "description": "Collect project highlights"
}
```

Titles are trimmed and limited to 200 characters. Descriptions are limited to 2,000 characters. Unknown fields and invalid statuses are rejected.

## Tests

Install the requirements, then run from the project root:

```powershell
py -m pytest
```

The tests cover task creation and retrieval, field validation, status updates, deletion, and missing IDs. They use a temporary SQLite database and do not modify the application database.
