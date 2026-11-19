"""Flask REST API for the Task Manager."""

import logging
import os
import sqlite3
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException, InternalServerError

from . import database
from .models import Task, current_timestamp, validate_task_input


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE=os.environ.get(
            "TASK_MANAGER_DATABASE", str(Path(__file__).with_name("tasks.db"))
        ),
        JSON_SORT_KEYS=False,
    )
    if test_config:
        app.config.update(test_config)
    database.initialize_database(app.config["DATABASE"])

    @app.after_request
    def add_cors_headers(response: Any) -> Any:
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException) -> Any:
        return jsonify(error=error.description), error.code

    @app.errorhandler(sqlite3.Error)
    def handle_database_error(error: sqlite3.Error) -> Any:
        app.logger.exception("Database operation failed: %s", error)
        return jsonify(error="A database error occurred."), 500

    @app.errorhandler(InternalServerError)
    def handle_internal_error(error: InternalServerError) -> Any:
        app.logger.error("Unhandled server error: %s", error)
        return jsonify(error="An unexpected server error occurred."), 500

    @app.get("/api/tasks")
    def get_tasks() -> Any:
        rows = database.list_tasks(app.config["DATABASE"])
        return jsonify(tasks=[Task.from_row(row).to_dict() for row in rows]), 200

    @app.post("/api/tasks")
    def post_task() -> Any:
        values, errors = validate_task_input(request.get_json(silent=True), creating=True)
        if errors:
            return jsonify(error="Invalid task data.", details=errors), 400
        row = database.create_task(
            app.config["DATABASE"],
            title=values["title"],
            description=values.get("description", ""),
            status="todo",
            created_at=current_timestamp(),
        )
        return jsonify(task=Task.from_row(row).to_dict()), 201

    @app.put("/api/tasks/<int:task_id>")
    def put_task(task_id: int) -> Any:
        values, errors = validate_task_input(request.get_json(silent=True), creating=False)
        if errors:
            return jsonify(error="Invalid task data.", details=errors), 400
        row = database.update_task(app.config["DATABASE"], task_id, values)
        if row is None:
            return jsonify(error="Task not found."), 404
        return jsonify(task=Task.from_row(row).to_dict()), 200

    @app.delete("/api/tasks/<int:task_id>")
    def remove_task(task_id: int) -> Any:
        if not database.delete_task(app.config["DATABASE"], task_id):
            return jsonify(error="Task not found."), 404
        return jsonify(message="Task deleted successfully."), 200

    return app


app = create_app()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(host="127.0.0.1", port=5000, debug=False)
