"""A small in-process job queue with progress reporting and cancellation.

Jobs run on a thread pool so FastAPI handlers return immediately. Heavy ML
work can later move to a process pool without changing the Job interface.
"""

from __future__ import annotations

import threading
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any


class JobCancelled(Exception):
    pass


@dataclass
class Job:
    id: str
    type: str
    status: str = "queued"
    progress: int = 0
    total: int = 0
    message: str | None = None
    error: str | None = None
    _cancel: threading.Event = field(default_factory=threading.Event, repr=False)

    def update(
        self, progress: int | None = None, total: int | None = None, message: str | None = None
    ) -> None:
        """Called by tasks to report progress; raises if the job was cancelled."""
        if self._cancel.is_set():
            raise JobCancelled
        if progress is not None:
            self.progress = progress
        if total is not None:
            self.total = total
        if message is not None:
            self.message = message

    def cancel(self) -> None:
        if self.status in ("queued", "running"):
            self._cancel.set()
            if self.status == "queued":
                self.status = "cancelled"

    @property
    def cancelled(self) -> bool:
        return self._cancel.is_set()

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "status": self.status,
            "progress": self.progress,
            "total": self.total,
            "message": self.message,
            "error": self.error,
        }


Task = Callable[..., Any]


class JobQueue:
    def __init__(self, max_workers: int = 2):
        self._pool = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="mote-job")
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def submit(self, job_type: str, task: Task, **kwargs: Any) -> Job:
        job = Job(id=uuid.uuid4().hex[:12], type=job_type)
        with self._lock:
            self._jobs[job.id] = job
        self._pool.submit(self._run, job, task, kwargs)
        return job

    def _run(self, job: Job, task: Task, kwargs: dict[str, Any]) -> None:
        if job.cancelled:
            job.status = "cancelled"
            return
        job.status = "running"
        try:
            task(job, **kwargs)
            job.status = "done"
        except JobCancelled:
            job.status = "cancelled"
        except Exception as exc:
            job.status = "failed"
            job.error = f"{type(exc).__name__}: {exc}"

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def list(self) -> list[Job]:
        with self._lock:
            return list(self._jobs.values())

    def shutdown(self) -> None:
        for job in self.list():
            job.cancel()
        self._pool.shutdown(wait=False, cancel_futures=True)
