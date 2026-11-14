"""Cancellation token for cooperative cancellation of in-flight operations.

This module provides a cancellation token mechanism that allows in-flight operations
to be cooperatively cancelled. The token propagates cancellation requests through
the operation lifecycle, enabling partial result returns and resource cleanup.
"""

import asyncio
import threading
from typing import Callable, Optional, Set


class CancellationToken:
    """A token that can be used to cooperatively cancel in-flight operations.

    The token supports cooperative cancellation where operations can check if
    cancellation has been requested and respond gracefully, returning partial
    results and cleaning up resources.

    Features:
    - Thread-safe cancellation checking
    - Cancel registration callbacks for resource cleanup
    - Propagated cancellation status
    - Non-blocking check
    - Callbacks invoked in LIFO order (last registered, first called)
    """

    def __init__(self, cancel_after: Optional[float] = None):
        """Initialize a cancellation token.

        Args:
            cancel_after: Optional seconds after which auto-cancellation occurs.
        """
        self._cancelled = False
        self._lock = threading.Lock()
        self._cancel_after = cancel_after
        self._timer: Optional[threading.Timer] = None
        self._registered_callbacks: list = []  # Maintains registration order
        self._event = threading.Event()

        # Start auto-cancel timer if specified
        if cancel_after is not None:
            self._schedule_auto_cancel()

    def _schedule_auto_cancel(self) -> None:
        """Schedule automatic cancellation after cancel_after seconds."""

        def _auto_cancel() -> None:
            with self._lock:
                self._cancelled = True
            self._event.set()
            self._invoke_callbacks()

        self._timer = threading.Timer(self._cancel_after, _auto_cancel)
        self._timer.start()

    @property
    def cancelled(self) -> bool:
        """Whether cancellation has been requested."""
        with self._lock:
            return self._cancelled

    @cancelled.setter
    def cancelled(self, value: bool) -> None:
        """Set the cancellation flag."""
        with self._lock:
            self._cancelled = value
        if value:
            self._event.set()

    def register_callback(self, callback: Callable[[], None]) -> None:
        """Register a callback to be invoked on cancellation.

        Callbacks are invoked for resource cleanup when cancellation occurs.
        Order of invocation is LIFO (last registered, first called).

        Args:
            callback: A no-argument callable to register.
        """
        self._registered_callbacks.append(callback)

    def unregister_callback(self, callback: Callable[[], None]) -> None:
        """Unregister a previously registered callback."""
        if callback in self._registered_callbacks:
            self._registered_callbacks.remove(callback)

    def cancel(self) -> None:
        """Request cancellation of the token."""
        with self._lock:
            self._cancelled = True
        self._event.set()
        self._invoke_callbacks()
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

    def _invoke_callbacks(self) -> None:
        """Invoke all registered cancellation callbacks in LIFO order."""
        # Invoke in reverse order (LIFO): last registered, first called
        for callback in reversed(self._registered_callbacks):
            try:
                callback()
            except Exception:
                # Swallow callback errors to avoid masking cancellation
                pass

    def check_cancel(self) -> bool:
        """Check if cancellation has been requested.

        Returns:
            True if cancellation was requested, False otherwise.
        """
        with self._lock:
            return self._cancelled

    def wait_cancel(self) -> bool:
        """Wait for cancellation to be requested.

        Returns:
            True when cancellation is requested.
        """
        self._event.wait()
        return True


class OperationContext:
    """Context manager for tracking an in-flight operation with cancellation support.

    Usage:
        async with OperationContext(token) as ctx:
            # do work, can check ctx.token.cancelled
            # on cancel, ctx returns partial status
    """

    def __init__(self, token: CancellationToken, operation_id: str):
        """Initialize operation context.

        Args:
            token: The cancellation token for this operation.
            operation_id: Unique identifier for the operation.
        """
        self.token = token
        self.operation_id = operation_id
        self._partial_result: Optional[object] = None
        self._cleanup_functions: list[Callable] = []

    def set_partial_result(self, result: object) -> None:
        """Set a partial result to be returned on cancellation."""
        self._partial_result = result

    def add_cleanup(self, func: Callable) -> None:
        """Add a cleanup function to run on cancellation or completion."""
        self._cleanup_functions.append(func)

    async def __aenter__(self):
        """Enter the context."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the context, handling cancellation if needed."""
        cancelled = self.token.cancelled or (exc_type is not None)
        if cancelled:
            # Invoke cleanup functions LIFO
            for func in reversed(self._cleanup_functions):
                try:
                    func()
                except Exception:
                    pass
            # Return partial result info via attribute
            return {"partial_result": self._partial_result, "cancelled": True}
        return None
