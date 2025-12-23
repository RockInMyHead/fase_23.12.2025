"""
Task management API routes
"""
from typing import List

from fastapi import APIRouter, HTTPException

from ...core.logging import get_logger
from ...core.state import app_state
from ...models.schemas import TaskResponse

logger = get_logger(__name__)
router = APIRouter()


@router.get("/list")
async def get_tasks():
    """
    Get all tasks
    """
    try:
        tasks = await app_state.list_tasks()
        # Map TaskState to TaskResponse format
        return [
            {
                "id": t.task_id,
                "status": t.status,
                "progress": t.progress,
                "message": t.message,
                "created_at": t.created_at,
                "completed_at": None  # TODO: add completed_at to TaskState
            }
            for t in tasks
        ]

    except Exception as e:
        logger.error(f"Failed to get tasks: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """
    Get specific task by ID

    Args:
        task_id: Task identifier
    """
    try:
        # TODO: Implement task retrieval by ID
        raise HTTPException(status_code=404, detail="Task not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/clear")
async def clear_completed_tasks():
    """
    Clear all completed tasks
    """
    try:
        await app_state.clear_tasks()
        return {"success": True}

    except Exception as e:
        logger.error(f"Failed to clear completed tasks: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
