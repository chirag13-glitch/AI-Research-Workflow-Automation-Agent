"""Task management API routes: creation, retrieval, SSE streaming, approval, and report exports."""
from datetime import datetime
import json
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse, PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.dependencies import get_db, get_current_user, verify_task_ownership
from backend.models.orm import User, Task, Source
from backend.models.schemas import (
    TaskCreate,
    TaskResponse,
    ApprovalRequest,
    ReportResponse,
    SourceMetadata,
    TaskStatus,
)
from backend.services.task_manager import task_manager

router = APIRouter(prefix="/api/v1/research/tasks", tags=["Research Tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a research topic and initiate execution."""
    task_id = f"task_{uuid.uuid4().hex[:12]}"
    new_task = Task(
        id=task_id,
        user_id=current_user.id,
        topic=payload.topic,
        status=TaskStatus.CREATED.value,
        constraints_json=json.dumps(payload.constraints),
        max_tool_calls=payload.max_tool_calls or 15,
        current_tool_calls=0,
        requires_approval=payload.require_human_approval,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    # Dispatch LangGraph background execution
    await task_manager.dispatch_task(
        task_id=task_id,
        topic=payload.topic,
        user_id=current_user.id,
        constraints=payload.constraints,
        max_tool_calls=payload.max_tool_calls or 15,
        require_human_approval=payload.require_human_approval,
    )

    return new_task


@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List research tasks owned by the authenticated user."""
    query = (
        select(Task)
        .where(Task.user_id == current_user.id)
        .order_by(Task.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve details and status for a specific task."""
    task = await verify_task_ownership(task_id, current_user, db)
    return task


@router.get("/{task_id}/events")
async def stream_task_events(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Server-Sent Events (SSE) live event stream for task execution."""
    await verify_task_ownership(task_id, current_user, db)
    return StreamingResponse(
        task_manager.subscribe_events(task_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{task_id}/sources", response_model=List[SourceMetadata])
async def get_task_sources(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve verified external sources collected for a task."""
    await verify_task_ownership(task_id, current_user, db)
    query = select(Source).where(Source.task_id == task_id)
    res = await db.execute(query)
    sources = res.scalars().all()
    return [
        SourceMetadata(
            source_id=s.source_id,
            url=s.url,
            title=s.title,
            domain=s.domain,
            retrieved_at=s.retrieved_at,
        )
        for s in sources
    ]


@router.get("/{task_id}/report", response_model=ReportResponse)
async def get_task_report(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve final report and citation verification audit."""
    task = await verify_task_ownership(task_id, current_user, db)
    if not task.report_markdown:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not generated yet for this task.",
        )

    # Fetch sources
    query = select(Source).where(Source.task_id == task_id)
    res = await db.execute(query)
    sources = res.scalars().all()
    source_metas = [
        SourceMetadata(
            source_id=s.source_id,
            url=s.url,
            title=s.title,
            domain=s.domain,
            retrieved_at=s.retrieved_at,
        )
        for s in sources
    ]

    cached = task_manager._cached_states.get(task_id, {})
    verification_results = cached.get("verification_results", [])
    grounding_score = cached.get("grounding_score", 1.0)
    verified_citations = sum(1 for c in verification_results if c.get("status") == "VERIFIED")

    return ReportResponse(
        task_id=task.id,
        topic=task.topic,
        content_markdown=task.report_markdown,
        sources=source_metas,
        citation_audit=verification_results,
        total_sources=len(source_metas),
        total_citations=len(verification_results),
        verified_citations=verified_citations,
        grounding_score=grounding_score,
    )


@router.get("/{task_id}/report/download")
async def download_report_markdown(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download report as raw Markdown file."""
    task = await verify_task_ownership(task_id, current_user, db)
    if not task.report_markdown:
        raise HTTPException(status_code=404, detail="Report not generated yet.")
    filename = f"report_{task_id}.md"
    return PlainTextResponse(
        content=task.report_markdown,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/{task_id}/approve")
async def approve_task_endpoint(
    task_id: str,
    payload: ApprovalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Approve or reject a task paused in AWAITING_APPROVAL."""
    task = await verify_task_ownership(task_id, current_user, db)
    resumed = await task_manager.approve_task(task_id, payload.approved, payload.feedback)
    if not resumed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task is not currently paused or cannot be resumed.",
        )
    return {"message": "Approval processed successfully", "approved": payload.approved}


@router.post("/{task_id}/cancel")
async def cancel_task_endpoint(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel an active task."""
    await verify_task_ownership(task_id, current_user, db)
    await task_manager.cancel_task(task_id)
    return {"message": f"Task {task_id} canceled successfully."}
