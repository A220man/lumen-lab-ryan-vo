"""Operation service with cooperative cancellation support.

This module provides services for managing in-flight operations with cancellation
token propagation, enabling partial result returns and resource cleanup on cancel.
"""

import asyncio
import uuid
from typing import Any, Dict, Optional, Callable

from app.core.cancellation import CancellationToken, OperationContext


class OperationService:
    """Service for managing in-flight operations with cancellation support."""

    def __init__(self):
        """Initialize the operation service."""
        self._operations: Dict[str, OperationContext] = {}
        self._lock = asyncio.Lock()

    async def start_operation(
        self,
        token: CancellationToken,
        operation_description: str,
    ) -> OperationContext:
        """Start tracking an in-flight operation.

        Args:
            token: The cancellation token for this operation.
            operation_description: Description of the operation for logging.

        Returns:
            An OperationContext for tracking and cancellation.
        """
        operation_id = str(uuid.uuid4())
        async with self._lock:
            ctx = OperationContext(token, operation_id)
            self._operations[operation_id] = ctx
        return ctx

    async def cancel_operation(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Cancel a running operation.

        Args:
            operation_id: The ID of the operation to cancel.

        Returns:
            Cancellation status dict with partial result info, or None if not found.
        """
        async with self._lock:
            ctx = self._operations.pop(operation_id, None)
        if ctx is None:
            return None

        # Request cancellation on the token
        ctx.token.cancel()

        # Invoke cleanup functions from the context (LIFO order)
        for func in reversed(ctx._cleanup_functions):
            try:
                func()
            except Exception:
                pass

        # Return cancellation status
        return {
            "operation_id": operation_id,
            "cancelled": True,
            "partial_result": ctx._partial_result,
            "cleanup_invoke": len(ctx._cleanup_functions),
        }

    def get_operation(self, operation_id: str) -> Optional[OperationContext]:
        """Get an operation context by ID.

        Args:
            operation_id: The operation ID to look up.

        Returns:
            The OperationContext, or None if not found.
        """
        return self._operations.get(operation_id)

    async def list_operations(self) -> list[Dict[str, str]]:
        """List all operation IDs currently being tracked.

        Returns:
            List of operation ID strings.
        """
        async with self._lock:
            return list(self._operations.keys())

    def set_partial_result(self, operation_id: str, result: object) -> bool:
        """Set a partial result for an operation.

        Args:
            operation_id: The operation ID.
            result: The partial result to return on cancellation.

        Returns:
            True if the result was set, False if operation not found.
        """
        ctx = self._operations.get(operation_id)
        if ctx is None:
            return False
        ctx.set_partial_result(result)
        return True

    def add_cleanup(self, operation_id: str, func: Callable) -> bool:
        """Add a cleanup function for an operation.

        Args:
            operation_id: The operation ID.
            func: The cleanup function to run on cancel/completion.

        Returns:
            True if cleanup was added, False if operation not found.
        """
        ctx = self._operations.get(operation_id)
        if ctx is None:
            return False
        ctx.add_cleanup(func)
        return True
