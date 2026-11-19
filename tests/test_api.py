"""API tests for task creation, retrieval, updates, and deletion."""

import pytest

from backend.app import create_app


@pytest.fixture()
def client(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "DATABASE": str(tmp_path / "test_tasks.db"),
        }
    )
    with app.test_client() as test_client:
        yield test_client


def test_create_and_retrieve_task(client):
    response = client.post(
        "/api/tasks",
        json={"title": "Plan launch", "description": "Review the checklist"},
    )

    assert response.status_code == 201
    task = response.get_json()["task"]
    assert task["title"] == "Plan launch"
    assert task["description"] == "Review the checklist"
    assert task["status"] == "todo"
    assert task["id"] > 0
    assert task["created_at"]

    listing = client.get("/api/tasks")
    assert listing.status_code == 200
    assert listing.get_json()["tasks"] == [task]


def test_create_task_rejects_invalid_input(client):
    for payload in ({}, {"title": "  "}, {"title": "Valid", "status": "done"}):
        response = client.post("/api/tasks", json=payload)
        assert response.status_code == 400
        assert response.get_json()["details"]


def test_create_task_rejects_non_object_json(client):
    response = client.post("/api/tasks", json=["not", "an", "object"])
    assert response.status_code == 400


def test_create_task_accepts_maximum_title_length(client):
    response = client.post("/api/tasks", json={"title": "x" * 200})
    assert response.status_code == 201
    assert len(response.get_json()["task"]["title"]) == 200

    too_long = client.post("/api/tasks", json={"title": "x" * 201})
    assert too_long.status_code == 400


def test_update_task_fields_and_reject_missing_id(client):
    task_id = client.post("/api/tasks", json={"title": "Draft"}).get_json()["task"]["id"]

    response = client.put(f"/api/tasks/{task_id}", json={"status": "in_progress"})
    assert response.status_code == 200
    assert response.get_json()["task"]["status"] == "in_progress"

    missing = client.put("/api/tasks/9999", json={"status": "done"})
    assert missing.status_code == 404
    assert missing.get_json()["error"] == "Task not found."


def test_update_rejects_invalid_status_and_empty_payload(client):
    task_id = client.post("/api/tasks", json={"title": "Draft"}).get_json()["task"]["id"]

    invalid_status = client.put(f"/api/tasks/{task_id}", json={"status": "blocked"})
    assert invalid_status.status_code == 400
    assert "status" in invalid_status.get_json()["details"]

    empty_update = client.put(f"/api/tasks/{task_id}", json={})
    assert empty_update.status_code == 400


def test_delete_task_and_missing_id(client):
    task_id = client.post("/api/tasks", json={"title": "Remove me"}).get_json()["task"]["id"]

    response = client.delete(f"/api/tasks/{task_id}")
    assert response.status_code == 200
    assert client.get("/api/tasks").get_json()["tasks"] == []

    missing = client.delete(f"/api/tasks/{task_id}")
    assert missing.status_code == 404


def test_in_memory_database_persists_across_requests():
    app = create_app({"TESTING": True, "DATABASE": ":memory:"})
    client = app.test_client()

    created = client.post("/api/tasks", json={"title": "Keep in memory"})
    assert created.status_code == 201

    listing = client.get("/api/tasks")
    assert listing.status_code == 200
    assert listing.get_json()["tasks"][0]["title"] == "Keep in memory"
