"""Tests for Phase 1: API endpoints, authentication, and task initialization."""
import pytest
import httpx
from backend.services.llm_adapter import MockLLM


@pytest.mark.asyncio
async def test_health_check(async_client: httpx.AsyncClient):
    """Test health endpoint returns healthy status and demo_mode=True."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["demo_mode"] is True
    assert data["database"] == "healthy"


@pytest.mark.asyncio
async def test_root_endpoint(async_client: httpx.AsyncClient):
    """Test root endpoint."""
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "SLURBUILDS" in data["message"]


@pytest.mark.asyncio
async def test_create_and_get_task(async_client: httpx.AsyncClient, user_headers: dict):
    """Test creating a research task and fetching it."""
    payload = {
        "topic": "Stateful Agent Architectures in Distributed Systems",
        "constraints": ["2024-2026", "peer-reviewed"],
        "max_tool_calls": 12,
        "require_human_approval": False,
    }
    response = await async_client.post("/api/v1/research/tasks", json=payload, headers=user_headers)
    assert response.status_code == 201
    created_task = response.json()
    assert created_task["id"].startswith("task_")
    assert created_task["topic"] == payload["topic"]
    assert created_task["status"] == "CREATED"
    assert created_task["max_tool_calls"] == 12

    # Fetch task
    get_res = await async_client.get(f"/api/v1/research/tasks/{created_task['id']}", headers=user_headers)
    assert get_res.status_code == 200
    fetched_data = get_res.json()
    assert fetched_data["id"] == created_task["id"]


@pytest.mark.asyncio
async def test_auth_invalid_key_rejected(async_client: httpx.AsyncClient, invalid_headers: dict):
    """Test that unauthorized requests are rejected."""
    payload = {"topic": "Quantum Machine Learning"}
    response = await async_client.post("/api/v1/research/tasks", json=payload, headers=invalid_headers)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_mock_llm_plan_deterministic():
    """Verify MockLLM returns structured, Pydantic-valid research plans."""
    plan = MockLLM.generate_plan(
        topic="Vector Indexing Strategies",
        constraints=["approximate nearest neighbor", "hnsw"],
    )
    assert len(plan.objectives) >= 3
    assert len(plan.subquestions) >= 3
    assert len(plan.search_queries) >= 3
    assert any("Vector Indexing Strategies" in obj for obj in plan.objectives)
