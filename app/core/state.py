"""
Application state management for in-memory storage.
For production with multiple workers, use Redis/database instead.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TaskState:
    """Represents a single background task state"""
    task_id: str
    folder_path: str
    status: str = "pending"     # pending|running|done|error
    progress: int = 0           # 0..100
    message: str = "В очереди..."
    created_at: float = field(default_factory=time.time)
    include_excluded: bool = False
    joint_mode: str = "copy"
    post_validate: bool = False
    error: Optional[str] = None


class AppState:
    """Unified in-memory state. Works for single-process mode (uvicorn without multiple workers)."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self.queue: List[str] = []
        self.current_tasks: Dict[str, TaskState] = {}
        self.task_history: List[TaskState] = []

    async def enqueue(self, folder_path: str) -> None:
        """Add folder to processing queue"""
        async with self._lock:
            if folder_path not in self.queue:
                self.queue.append(folder_path)

    async def get_queue(self) -> List[str]:
        """Get current queue"""
        async with self._lock:
            return list(self.queue)

    async def clear_queue(self) -> None:
        """Clear processing queue"""
        async with self._lock:
            self.queue.clear()

    async def upsert_task(self, t: TaskState) -> None:
        """Insert or update task"""
        async with self._lock:
            self.current_tasks[t.task_id] = t

    async def set_task_status(
        self,
        task_id: str,
        status: str,
        message: str = "",
        progress: Optional[int] = None,
        error: Optional[str] = None
    ) -> None:
        """Update task status"""
        async with self._lock:
            t = self.current_tasks.get(task_id)
            if not t:
                return
            t.status = status
            if message:
                t.message = message
            if progress is not None:
                t.progress = progress
            if error is not None:
                t.error = error

            if status in ("done", "error"):
                # Move to history
                self.task_history.append(t)
                self.current_tasks.pop(task_id, None)

    async def list_tasks(self) -> List[TaskState]:
        """List all current tasks"""
        async with self._lock:
            # Return active tasks + optionally history
            return list(self.current_tasks.values())

    async def clear_tasks(self) -> None:
        """Clear all tasks"""
        async with self._lock:
            self.current_tasks.clear()
            self.task_history.clear()


# Global state instance
app_state = AppState()
