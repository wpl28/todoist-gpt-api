import os
import requests

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()

TODOIST_API_TOKEN = os.getenv("TODOIST_API_TOKEN")
TODOIST_API_URL = "https://api.todoist.com/api/v1"

app = FastAPI(

    title="Witek Todoist GPT API",
    servers=[
        {
            "url": "https://todoist-gpt-api.onrender.com"
        }
    ]
)


class TaskCreate(BaseModel):
    content: str
    project_id: str | None = None
    due_string: str | None = None
    priority: int | None = None

class TaskUpdate(BaseModel):
    content: str | None = None
    due_string: str | None = None
    priority: int | None = None


def get_headers():
    if not TODOIST_API_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="Missing TODOIST_API_TOKEN in .env file"
        )

    return {
        "Authorization": f"Bearer {TODOIST_API_TOKEN}",
        "Content-Type": "application/json",
    }


def todoist_get(endpoint: str, params: dict | None = None):
    response = requests.get(
        f"{TODOIST_API_URL}{endpoint}",
        headers=get_headers(),
        params=params
    )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text
        )

    return response.json()


def todoist_post(endpoint: str, payload: dict | None = None):
    response = requests.post(
        f"{TODOIST_API_URL}{endpoint}",
        headers=get_headers(),
        json=payload
    )

    if response.status_code not in [200, 201, 204]:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text
        )

    if response.status_code == 204:
        return {"message": "OK"}

    return response.json()


def todoist_delete(endpoint: str):
    response = requests.delete(
        f"{TODOIST_API_URL}{endpoint}",
        headers=get_headers()
    )

    if response.status_code != 204:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text
        )

    return {"message": "Deleted"}


@app.get("/")
def home():
    return {
        "message": "Witek Todoist GPT API działa",
        "docs": "http://127.0.0.1:8000/docs"
    }


@app.get("/projects")
def get_projects():
    raw = todoist_get("/projects")

    projects = raw.get("results", raw)

    return [
        {
            "id": project["id"],
            "name": project["name"]
        }
        for project in projects
    ]


@app.get("/tasks")
def get_tasks(project_id: str | None = None):
    params = {}

    if project_id:
        params["project_id"] = project_id

    raw = todoist_get("/tasks", params=params)

    tasks = raw.get("results", raw)

    return [
        {
            "id": task["id"],
            "content": task["content"],
            "project_id": task.get("project_id"),
            "due": task.get("due"),
            "priority": task.get("priority"),
            "is_completed": task.get("is_completed", False)
        }
        for task in tasks
    ]


@app.post("/tasks")
def create_task(task: TaskCreate):
    payload = {
        "content": task.content
    }

    if task.project_id:
        payload["project_id"] = task.project_id

    if task.due_string:
        payload["due_string"] = task.due_string

    if task.priority:
        payload["priority"] = task.priority

    return todoist_post("/tasks", payload)


@app.post("/tasks/{task_id}/close")
def close_task(task_id: str):
    return todoist_post(f"/tasks/{task_id}/close")


@app.delete("/tasks/{task_id}")
def delete_task(task_id: str):
    return todoist_delete(f"/tasks/{task_id}")


@app.patch("/tasks/{task_id}")
def update_task(task_id: str, task: TaskUpdate):
    payload = {}

    if task.content:
        payload["content"] = task.content

    if task.due_string:
        payload["due_string"] = task.due_string

    if task.priority:
        payload["priority"] = task.priority

    if not payload:
        raise HTTPException(
            status_code=400,
            detail="No fields to update"
        )

    return todoist_post(f"/tasks/{task_id}", payload)