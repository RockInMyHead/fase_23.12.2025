"""
Clustering operations API routes
"""
import time
import uuid
import asyncio
from pathlib import Path

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query

from ...core.logging import get_logger
from ...core.state import app_state, TaskState
from ...models.schemas import QueueItemRequest, ProcessCommonPhotosRequest
from ...services.legacy_processing import run_process_folder_task
from ...services.clustering import get_clustering_service

logger = get_logger(__name__)
router = APIRouter()


async def _runner(task_id: str, folder_path: str, include_excluded: bool, joint_mode: str, post_validate: bool) -> None:
    """Background task runner for legacy processing"""
    # Mark start
    await app_state.set_task_status(task_id, "running", message="Обработка запущена...", progress=1)
    try:
        # If legacy contains CPU-heavy code that blocks event loop - wrap in asyncio.to_thread if needed
        await run_process_folder_task(task_id, folder_path, include_excluded, joint_mode, post_validate)
        await app_state.set_task_status(task_id, "done", message="Готово", progress=100)
    except Exception as e:
        logger.exception("Task failed: %s", task_id)
        await app_state.set_task_status(task_id, "error", message="Ошибка", error=str(e))


@router.post("/queue")
@router.post("/queue/add")  # Alias for frontend compatibility
async def add_to_queue(
    item: QueueItemRequest,
    includeExcluded: bool = Query(False, description="Include excluded folders")
):
    """
    Add folder to processing queue

    Args:
        item: Queue item request
        includeExcluded: Whether to include excluded folders
    """
    try:
        folder_path = Path(item.path)

        if not folder_path.exists():
            raise HTTPException(status_code=404, detail="Folder not found")

        if not folder_path.is_dir():
            raise HTTPException(status_code=400, detail="Path is not a directory")

        # Add to queue
        await app_state.enqueue(str(folder_path))

        return {
            "success": True,
            "message": f"Added {folder_path.name} to queue"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add to queue: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/queue")
async def get_queue():
    """
    Get current processing queue
    """
    try:
        queue = await app_state.get_queue()
        return {
            "queue": queue,
            "total": len(queue)
        }

    except Exception as e:
        logger.error(f"Failed to get queue: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/queue")
async def clear_queue():
    """
    Clear processing queue
    """
    try:
        await app_state.clear_queue()
        return {"success": True}

    except Exception as e:
        logger.error(f"Failed to clear queue: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/process-queue")
@router.post("/process")  # Alias for old frontend (if it calls /api/process)
async def process_queue(
    background_tasks: BackgroundTasks,
    includeExcluded: bool = Query(False, description="Include excluded folders"),
    jointMode: str = Query("copy", description="Joint photo mode"),
    postValidate: bool = Query(False, description="Post-validation enabled")
):
    """
    Start processing the queue (local clustering)

    Args:
        background_tasks: FastAPI background tasks
        includeExcluded: Include excluded folders
        jointMode: How to handle joint photos ('copy' or 'move')
        postValidate: Enable post-validation
    """
    try:
        queue = await app_state.get_queue()
        if not queue:
            raise HTTPException(status_code=400, detail="Очередь пуста")

        task_ids = []
        for folder_path in queue:
            task_id = str(uuid.uuid4())

            t = TaskState(
                task_id=task_id,
                folder_path=folder_path,
                status="pending",
                progress=0,
                message="В очереди...",
                include_excluded=includeExcluded,
                joint_mode=jointMode,
                post_validate=postValidate,
                created_at=time.time(),
            )
            await app_state.upsert_task(t)

            # Start in background
            background_tasks.add_task(_runner, task_id, folder_path, includeExcluded, jointMode, postValidate)
            task_ids.append(task_id)

        await app_state.clear_queue()
        return {"message": "Обработка запущена", "task_ids": task_ids}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start queue processing: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/process-global")
async def process_global_queue(background_tasks: BackgroundTasks):
    """
    Start global clustering processing
    """
    try:
        # TODO: Implement global clustering
        task_id = "global_clustering_task"

        background_tasks.add_task(
            process_global_clustering_task,
            task_id
        )

        return {
            "task_id": task_id,
            "message": "Global clustering started"
        }

    except Exception as e:
        logger.error(f"Failed to start global clustering: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/process-common")
async def process_common_photos(request: ProcessCommonPhotosRequest):
    """
    Process common photos between groups
    """
    try:
        # TODO: Implement common photos processing
        return {
            "success": True,
            "message": "Common photos processing started"
        }

    except Exception as e:
        logger.error(f"Failed to process common photos: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def process_local_clustering_task(
    task_id: str,
    include_excluded: bool,
    joint_mode: str,
    post_validate: bool
):
    """Background task for local clustering"""
    try:
        logger.info(f"Starting local clustering task {task_id}")

        # TODO: Implement actual local clustering logic

        logger.info(f"Completed local clustering task {task_id}")

    except Exception as e:
        logger.error(f"Local clustering task {task_id} failed: {e}")
        # TODO: Update task status


async def process_global_clustering_task(task_id: str):
    """Background task for global clustering"""
    try:
        logger.info(f"Starting global clustering task {task_id}")

        # TODO: Implement actual global clustering logic

        logger.info(f"Completed global clustering task {task_id}")

    except Exception as e:
        logger.error(f"Global clustering task {task_id} failed: {e}")
        # TODO: Update task status
