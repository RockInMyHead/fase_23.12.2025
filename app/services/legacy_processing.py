"""
Legacy processing bridge for existing clustering functionality.
Imports and wraps old process_folder_task function.
"""
import asyncio
from typing import Any

from ..core.state import app_state as new_app_state

# WARNING: Import function from old monolithic code.
# Adjust path according to your actual module/package.
try:
    from main import process_folder_task as legacy_process_folder_task
    from main import app_state as old_app_state
except ImportError:
    # Fallback if import fails
    legacy_process_folder_task = None
    old_app_state = None


async def run_process_folder_task(task_id: str, *args: Any, **kwargs: Any) -> None:
    """
    Run legacy async task. If it contains CPU-heavy code inside,
    better to move to to_thread, but for now minimally preserve behavior.

    This function bridges between new and old state management.
    """
    if legacy_process_folder_task is None:
        raise RuntimeError("Legacy process_folder_task not available")

    # Sync task state from new to old state before processing
    tasks = await new_app_state.list_tasks()
    task = next((t for t in tasks if t.task_id == task_id), None)

    if task and old_app_state is not None:
        # Create task in old app_state to make legacy code work
        old_app_state["current_tasks"][task_id] = {
            "task_id": task_id,
            "status": task.status,
            "progress": task.progress,
            "message": task.message,
            "folder_path": task.folder_path,
            "created_at": task.created_at,
            "include_excluded": task.include_excluded
        }

    try:
        print(f"🔄 [LEGACY] Запуск обработки задачи {task_id}")
        await legacy_process_folder_task(task_id, *args, **kwargs)
        print(f"✅ [LEGACY] Обработка задачи {task_id} завершена")
    except Exception as e:
        print(f"❌ [LEGACY] Ошибка в задаче {task_id}: {e}")
        raise
    finally:
        # Sync state back from old to new after processing
        if old_app_state is not None and task_id in old_app_state["current_tasks"]:
            old_task = old_app_state["current_tasks"][task_id]
            print(f"🔄 [LEGACY] Синхронизация состояния задачи {task_id}: status={old_task.get('status')}")
            await new_app_state.set_task_status(
                task_id,
                old_task.get("status", "error"),
                old_task.get("message", "Completed"),
                old_task.get("progress", 100),
                old_task.get("error")
            )
        elif task_id not in old_app_state.get("current_tasks", {}):
            # If task not in old state, check if it completed successfully
            # This handles cases where task finished but wasn't in old state
            print(f"⚠️ [LEGACY] Задача {task_id} не найдена в old_app_state, устанавливаем completed")
            await new_app_state.set_task_status(
                task_id,
                "completed",
                "Обработка завершена успешно",
                100,
                None
            )
        else:
            print(f"⚠️ [LEGACY] Задача {task_id} не найдена в обоих состояниях")
