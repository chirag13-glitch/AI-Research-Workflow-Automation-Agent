"""Allowlisted tool registry with execution budget tracking and concurrency limits."""
import asyncio
from typing import Any, Callable, Dict, Optional
from backend.config import get_settings
from backend.tools.web_search import execute_web_search
from backend.tools.page_fetcher import fetch_web_page
from backend.tools.content_extractor import extract_html_text

settings = get_settings()


class ToolExecutionBudgetExceeded(Exception):
    """Raised when total tool calls exceed the assigned task budget."""
    pass


class ToolRegistry:
    """Central allowlist and execution dispatcher for agent tools."""

    def __init__(self, max_concurrent: int = 3):
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._allowed_tools: Dict[str, Callable] = {
            "web_search": execute_web_search,
            "fetch_web_page": fetch_web_page,
            "extract_html_text": extract_html_text,
        }

    def is_allowed(self, tool_name: str) -> bool:
        return tool_name in self._allowed_tools

    async def execute(
        self,
        tool_name: str,
        kwargs: Dict[str, Any],
        current_calls: int,
        max_calls: int,
    ) -> Dict[str, Any]:
        """
        Validate allowlist, enforce budget, acquire concurrency semaphore, and execute tool.
        """
        if not self.is_allowed(tool_name):
            return {
                "success": False,
                "error": f"Tool '{tool_name}' is not in the allowlist. Allowed: {list(self._allowed_tools.keys())}",
                "result": None,
            }

        if current_calls >= max_calls:
            raise ToolExecutionBudgetExceeded(
                f"Tool execution budget exhausted: {current_calls}/{max_calls} calls completed."
            )

        tool_fn = self._allowed_tools[tool_name]

        async with self._semaphore:
            try:
                if asyncio.iscoroutinefunction(tool_fn):
                    result = await tool_fn(**kwargs)
                else:
                    result = tool_fn(**kwargs)
                return {
                    "success": True,
                    "error": None,
                    "result": result,
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Error executing tool '{tool_name}': {str(e)}",
                    "result": None,
                }


# Global registry instance
tool_registry = ToolRegistry(max_concurrent=settings.MAX_CONCURRENT_TOOL_CALLS)
