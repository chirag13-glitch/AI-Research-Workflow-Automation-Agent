"""Task execution manager: handles background LangGraph execution, checkpoint resumption, and SSE broadcasting."""
import asyncio
from datetime import datetime
import json
from typing import Any, AsyncGenerator, Dict, List, Optional, Set
from sqlalchemy import select
from backend.agents.graph import get_compiled_graph
from backend.agents.state import ResearchAgentState
from backend.config import get_settings
from backend.db.session import AsyncSessionLocal
from backend.models.orm import Task, StepLog, Source
from backend.models.schemas import TaskStatus

settings = get_settings()


class TaskManager:
    """Manages active task lifecycles, event queues, and LangGraph checkpoints."""

    def __init__(self):
        # Map: task_id -> list of asyncio.Queue for connected SSE clients
        self._listeners: Dict[str, Set[asyncio.Queue]] = {}
        # Map: task_id -> running asyncio.Task
        self._running_tasks: Dict[str, asyncio.Task] = {}
        # Map: task_id -> latest state
        self._cached_states: Dict[str, ResearchAgentState] = {}

    def _get_listeners(self, task_id: str) -> Set[asyncio.Queue]:
        if task_id not in self._listeners:
            self._listeners[task_id] = set()
        return self._listeners[task_id]

    async def broadcast_event(self, task_id: str, event_data: Dict[str, Any]):
        """Publish an event to all SSE streams listening to task_id."""
        listeners = list(self._get_listeners(task_id))
        for q in listeners:
            try:
                await q.put(event_data)
            except Exception:
                pass

    async def subscribe_events(self, task_id: str) -> AsyncGenerator[str, None]:
        """Async generator providing SSE-formatted events for a task."""
        q = asyncio.Queue()
        self._get_listeners(task_id).add(q)
        try:
            # Yield initial connection message
            yield f"data: {json.dumps({'event': 'CONNECTED', 'task_id': task_id})}\n\n"
            while True:
                event = await q.get()
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("status") in (
                    TaskStatus.COMPLETED.value,
                    TaskStatus.FAILED.value,
                    TaskStatus.CANCELED.value,
                ):
                    break
        finally:
            self._get_listeners(task_id).discard(q)

    async def run_graph(self, initial_state: ResearchAgentState):
        """Execute the LangGraph workflow in background, persisting steps to DB."""
        task_id = initial_state["task_id"]
        config = {"configurable": {"thread_id": task_id}}
        compiled_graph = get_compiled_graph()

        async def _save_db_step(step_entry: Dict[str, Any]):
            async with AsyncSessionLocal() as db:
                step = StepLog(
                    task_id=task_id,
                    node_name=step_entry.get("node", "system"),
                    status=step_entry.get("status", "INFO"),
                    log_message=step_entry.get("message", ""),
                    created_at=datetime.utcnow(),
                )
                db.add(step)
                await db.commit()

        try:
            # Execute step-by-step
            current_state = initial_state
            async for event in compiled_graph.astream(initial_state, config=config, stream_mode="updates"):
                for node_name, node_update in event.items():
                    current_state = {**current_state, **node_update}
                    self._cached_states[task_id] = current_state

                    status = current_state.get("status", "RUNNING")
                    last_step = current_state.get("step_history", [{}])[-1]

                    # Broadcast SSE
                    broadcast_payload = {
                        "task_id": task_id,
                        "node": node_name,
                        "status": status,
                        "message": last_step.get("message", f"Finished {node_name}"),
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                    await self.broadcast_event(task_id, broadcast_payload)
                    await _save_db_step(last_step)

                    # Update Task status in DB
                    async with AsyncSessionLocal() as db:
                        t = await db.get(Task, task_id)
                        if t:
                            t.status = status
                            t.current_tool_calls = current_state.get("current_tool_calls", 0)
                            t.requires_approval = current_state.get("requires_approval", False)
                            t.approval_reason = current_state.get("approval_reason")
                            t.updated_at = datetime.utcnow()
                            if status == TaskStatus.AWAITING_APPROVAL.value:
                                t.approval_status = "PENDING"
                            await db.commit()

            # Finalize completed task
            final_report = current_state.get("final_report_markdown")
            final_sources = current_state.get("collected_sources", {})

            async with AsyncSessionLocal() as db:
                t = await db.get(Task, task_id)
                if t:
                    t.status = current_state.get("status", TaskStatus.COMPLETED.value)
                    t.report_markdown = final_report
                    t.plan_json = json.dumps(current_state.get("plan", {}))
                    t.completed_at = datetime.utcnow()
                    t.updated_at = datetime.utcnow()

                    # Save sources
                    for s_id, s_meta in final_sources.items():
                        source_rec = Source(
                            task_id=task_id,
                            source_id=s_id,
                            url=s_meta.get("url", ""),
                            title=s_meta.get("title", ""),
                            domain=s_meta.get("domain", ""),
                            retrieved_at=datetime.utcnow(),
                        )
                        db.add(source_rec)

                    await db.commit()

            # Final broadcast
            await self.broadcast_event(task_id, {
                "task_id": task_id,
                "node": "system",
                "status": current_state.get("status", TaskStatus.COMPLETED.value),
                "message": "Task completed successfully",
                "timestamp": datetime.utcnow().isoformat(),
            })

        except asyncio.CancelledError:
            async with AsyncSessionLocal() as db:
                t = await db.get(Task, task_id)
                if t:
                    t.status = TaskStatus.CANCELED.value
                    t.updated_at = datetime.utcnow()
                    await db.commit()
            await self.broadcast_event(task_id, {
                "task_id": task_id,
                "node": "system",
                "status": TaskStatus.CANCELED.value,
                "message": "Task was canceled by user",
                "timestamp": datetime.utcnow().isoformat(),
            })
        except Exception as e:
            async with AsyncSessionLocal() as db:
                t = await db.get(Task, task_id)
                if t:
                    t.status = TaskStatus.FAILED.value
                    t.error_message = str(e)
                    t.updated_at = datetime.utcnow()
                    await db.commit()
            await self.broadcast_event(task_id, {
                "task_id": task_id,
                "node": "system",
                "status": TaskStatus.FAILED.value,
                "message": f"Execution failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
            })
        finally:
            self._running_tasks.pop(task_id, None)

    async def dispatch_task(
        self,
        task_id: str,
        topic: str,
        user_id: str,
        constraints: List[str],
        max_tool_calls: int = 15,
        require_human_approval: bool = False,
    ):
        """Initialize state and spawn background execution."""
        initial_state: ResearchAgentState = {
            "task_id": task_id,
            "topic": topic,
            "user_id": user_id,
            "constraints": constraints,
            "max_tool_calls": max_tool_calls,
            "current_tool_calls": 0,
            "retry_count": 0,
            "max_retries": 2,
            "require_human_approval": require_human_approval,
            "plan": None,
            "subquestions": [],
            "active_queries": [],
            "raw_tool_results": [],
            "collected_sources": {},
            "evidence_chunks": [],
            "conflicting_evidence": [],
            "requires_approval": False,
            "approval_reason": None,
            "approval_status": None,
            "approval_feedback": None,
            "draft_report_markdown": None,
            "verification_results": [],
            "final_report_markdown": None,
            "grounding_score": 0.0,
            "status": TaskStatus.CREATED.value,
            "errors": [],
            "step_history": [],
        }

        self._cached_states[task_id] = initial_state
        task_coro = asyncio.create_task(self.run_graph(initial_state))
        self._running_tasks[task_id] = task_coro

    async def approve_task(self, task_id: str, approved: bool, feedback: Optional[str] = None):
        """Approve and resume task, or reject and cancel."""
        state = self._cached_states.get(task_id)
        if not state:
            return False

        if approved:
            resumed_state: ResearchAgentState = {
                **state,
                "approval_status": "APPROVED",
                "requires_approval": False,
                "approval_feedback": feedback,
            }
            self._cached_states[task_id] = resumed_state
            # Re-spawn graph from resumed state
            task_coro = asyncio.create_task(self.run_graph(resumed_state))
            self._running_tasks[task_id] = task_coro
            return True
        else:
            await self.cancel_task(task_id)
            return True

    async def cancel_task(self, task_id: str):
        """Safely cancel an active task."""
        running = self._running_tasks.get(task_id)
        if running and not running.done():
            running.cancel()
        else:
            async with AsyncSessionLocal() as db:
                t = await db.get(Task, task_id)
                if t:
                    t.status = TaskStatus.CANCELED.value
                    await db.commit()


task_manager = TaskManager()
