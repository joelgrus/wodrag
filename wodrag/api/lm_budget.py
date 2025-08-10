"""Per-request LLM call budgeting for DSPy LM usage.

This module provides a thin wrapper around a DSPy LM object that enforces
an upper bound on the number of LM invocations per HTTP request. It uses
contextvars so each incoming request gets its own counter.
"""

from __future__ import annotations

import os
from contextvars import ContextVar
from types import MethodType
from typing import Any

from wodrag.conversation.models import ConversationValidationError

# Context variables to track LM usage per request
_lm_calls: ContextVar[int] = ContextVar("lm_calls", default=0)
_lm_budget: ContextVar[int] = ContextVar(
    "lm_budget",
    default=int(os.getenv("PER_REQUEST_LM_CALL_BUDGET", "6")),
)


def reset_request_lm_budget(budget: int | None = None) -> None:
    """Reset the per-request LM call counter and set budget if provided."""
    _lm_calls.set(0)
    if budget is not None:
        _lm_budget.set(int(budget))


def increment_and_check_budget() -> None:
    """Increment LM call count and raise if exceeding the budget."""
    calls = _lm_calls.get()
    budget = _lm_budget.get()
    new_calls = calls + 1
    _lm_calls.set(new_calls)
    if new_calls > budget:
        raise ConversationValidationError(
            "Rate limit exceeded: per-request LLM call budget reached."
        )


def wrap_lm_for_budget(lm: Any) -> Any:
    """Monkey-patch an LM instance to enforce per-request budget on calls.

    This avoids subclassing DSPy's internal BaseLM and keeps compatibility.
    """
    original_call = lm.__call__

    def _wrapped(self: Any, *args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
        increment_and_check_budget()
        return original_call(*args, **kwargs)

    # Bind as a method on this instance
    lm.__call__ = MethodType(_wrapped, lm)
    return lm
