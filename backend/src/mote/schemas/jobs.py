from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

JobStatus = Literal["queued", "running", "done", "failed", "cancelled"]


class JobOut(BaseModel):
    id: str
    type: str
    status: JobStatus
    progress: int
    total: int
    message: str | None
    error: str | None
