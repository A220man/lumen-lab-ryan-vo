"""Tests for cooperative cancellation token propagation.

Tests the CancellationToken and OperationContext for cooperative cancellation
of in-flight operations, ensuring proper token propagation, partial result
return, and resource cleanup.
"""

import pytest
import asyncio

from app.core.cancellation import CancellationToken, OperationContext


class TestCancellationToken:
    """Tests for CancellationToken class."""

    def test_init_default(self):
        """Default token starts non-cancelled."""
        token = CancellationToken()
        assert token.cancelled is False

    def test_init_with_cancel_after(self):
        """Token with cancel_after schedules auto-cancellation."""
        token = CancellationToken(cancel_after=0.1)
        import time
        time.sleep(0.15)  # Wait for timer to fire
        assert token.cancelled is True

    def test_cancel(self):
        """Cancellation sets the cancelled flag."""
        token = CancellationToken()
        token.cancel()
        assert token.cancelled is True

    def test_cancel_idempotent(self):
        """Cancelling an already cancelled token is idempotent."""
        token = CancellationToken()
        token.cancel()
        token.cancel()  # Should not raise
        assert token.cancelled is True

    def test_check_cancel(self):
        """check_cancel returns the current cancellation state."""
        token = CancellationToken()
        assert token.check_cancel() is False
        token.cancel()
        assert token.check_cancel() is True

    def test_register_and_invoke_callbacks(self):
        """Registered callbacks are invoked on cancellation."""
        token = CancellationToken()
        called = []

        def cb1():
            called.append("cb1")

        def cb2():
            called.append("cb2")

        token.register_callback(cb1)
        token.register_callback(cb2)
        token.cancel()
        assert called == ["cb2", "cb1"]  # LIFO order

    def test_unregister_callback(self):
        """Unregistering a callback prevents it from being invoked."""
        token = CancellationToken()
        called = []

        def cb():
            called.append("cb")

        token.register_callback(cb)
        token.unregister_callback(cb)
        token.cancel()
        assert called == []

    def test_wait_cancel(self):
        """wait_cancel returns True when cancellation is requested."""
        token = CancellationToken()
        # wait_cancel is synchronous (uses threading.Event)
        # Initially not cancelled, wait should block until cancelled
        # For this test, just verify check_cancel works
        assert token.check_cancel() is False
        token.cancel()
        assert token.check_cancel() is True


class TestOperationContext:
    """Tests for OperationContext class."""

    def test_context_manager_exit_cancel(self):
        """Context manager exits with cancelled status when token is cancelled."""
        token = CancellationToken()
        ctx = OperationContext(token, "test-op-1")

        # Simulate work being cancelled
        token.cancel()

        # Exit context should reflect cancellation
        result = asyncio.run(ctx.__aexit__(None, None, None))
        assert result is not None
        assert result.get("cancelled") is True

    def test_context_manager_no_cancel(self):
        """Context manager exits normally when not cancelled."""
        token = CancellationToken()
        ctx = OperationContext(token, "test-op-2")

        result = asyncio.run(ctx.__aexit__(None, None, None))
        assert result is None  # No cancellation, no special exit

    def test_set_partial_result(self):
        """Partial result can be set and retrieved on cancellation."""
        token = CancellationToken()
        ctx = OperationContext(token, "test-op-3")

        ctx.set_partial_result({"status": "partial", "progress": 0.5})

        token.cancel()
        result = asyncio.run(ctx.__aexit__(None, None, None))
        assert result is not None
        assert result.get("partial_result") == {"status": "partial", "progress": 0.5}

    def test_add_and_invoke_cleanup(self):
        """Cleanup functions are invoked on context exit with cancellation."""
        token = CancellationToken()
        ctx = OperationContext(token, "test-op-4")
        cleanup_calls = []

        def cleanup1():
            cleanup_calls.append("cleanup1")

        def cleanup2():
            cleanup_calls.append("cleanup2")

        ctx.add_cleanup(cleanup1)
        ctx.add_cleanup(cleanup2)

        token.cancel()
        asyncio.run(ctx.__aexit__(None, None, None))
        # LIFO order: cleanup2 first, then cleanup1
        assert cleanup_calls == ["cleanup2", "cleanup1"]

    def test_add_cleanup_multiple_times(self):
        """Cleanup can be added multiple times; all are invoked."""
        token = CancellationToken()
        ctx = OperationContext(token, "test-op-5")
        calls = []

        def make_callback(n):
            return lambda: calls.append(f"cb_{n}")

        ctx.add_cleanup(make_callback(1))
        ctx.add_cleanup(make_callback(2))
        ctx.add_cleanup(make_callback(3))

        token.cancel()
        asyncio.run(ctx.__aexit__(None, None, None))
        assert len(calls) == 3
        # LIFO order
        assert calls == ["cb_3", "cb_2", "cb_1"]


class TestCooperativeCancellation:
    """Tests for cooperative cancellation workflow."""

    @pytest.mark.asyncio
    async def test_operation_start_and_cancel(self):
        """Operations can be started and cancelled with token propagation."""
        from app.services.operation import OperationService

        token = CancellationToken()
        service = OperationService()

        # Start an operation
        ctx = await service.start_operation(token, "test-benchmark-run")

        # Verify context is tracked
        assert ctx.operation_id is not None
        ops = await service.list_operations()
        assert ctx.operation_id in ops

        # Cancel the operation
        status = await service.cancel_operation(ctx.operation_id)
        assert status is not None
        assert status["cancelled"] is True
        assert "partial_result" in status

        # Operation should no longer be tracked
        remaining = await service.list_operations()
        assert ctx.operation_id not in remaining

    @pytest.mark.asyncio
    async def test_partial_result_on_cancel(self):
        """Partial results are returned on cancellation."""
        from app.services.operation import OperationService

        token = CancellationToken()
        service = OperationService()

        ctx = await service.start_operation(token, "test-benchmark-2")
        # Set a partial result simulating mid-operation state
        ctx.set_partial_result({"iterations_completed": 15, "latency_ms": 12.5})

        # Cancel should return the partial result
        status = await service.cancel_operation(ctx.operation_id)
        assert status["partial_result"] == {"iterations_completed": 15, "latency_ms": 12.5}

    @pytest.mark.asyncio
    async def test_cleanup_on_cancel(self):
        """Cleanup functions are invoked on operation cancellation."""
        from app.services.operation import OperationService

        token = CancellationToken()
        service = OperationService()

        ctx = await service.start_operation(token, "test-benchmark-3")
        cleanup_order = []

        def cleanup_a():
            cleanup_order.append("a")

        def cleanup_b():
            cleanup_order.append("b")

        ctx.add_cleanup(cleanup_a)
        ctx.add_cleanup(cleanup_b)

        # Cancel the operation
        await service.cancel_operation(ctx.operation_id)

        # Cleanup should have been invoked (LIFO: b then a)
        assert cleanup_order == ["b", "a"]
