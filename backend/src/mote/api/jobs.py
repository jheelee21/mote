from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from mote.schemas.jobs import JobOut

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=list[JobOut])
def list_jobs(request: Request) -> list[JobOut]:
    return [JobOut(**j.as_dict()) for j in request.app.state.jobs.list()]


@router.get("/events")
async def job_events(request: Request) -> StreamingResponse:
    """Server-sent events: one `data:` line per job update."""
    queue = request.app.state.jobs

    async def stream():
        last_seen: dict[str, tuple] = {}
        while not await request.is_disconnected():
            for job in queue.list():
                d = job.as_dict()
                key = (d["status"], d["progress"], d["total"])
                if last_seen.get(d["id"]) != key:
                    last_seen[d["id"]] = key
                    yield f"data: {json.dumps(d)}\n\n"
            await asyncio.sleep(0.5)

    return StreamingResponse(stream(), media_type="text/event-stream")


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: str, request: Request) -> JobOut:
    job = request.app.state.jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return JobOut(**job.as_dict())


@router.post("/{job_id}/cancel", response_model=JobOut)
def cancel_job(job_id: str, request: Request) -> JobOut:
    job = request.app.state.jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    job.cancel()
    return JobOut(**job.as_dict())
