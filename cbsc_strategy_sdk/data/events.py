"""Event emitter for real-time data streaming.

Provides callback-based event system for WebSocket client.
"""

from collections import defaultdict
from typing import Any, Callable, Coroutine, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)


class EventEmitter:
    """Generic event emitter for real-time updates.

    Provides a simple callback-based event system that supports both
    synchronous and asynchronous callbacks.

    Example:
        >>> emitter = EventEmitter()
        >>> def on_tick(tick):
        ...     print(f"Received: {tick}")
        >>> emitter.on('tick', on_tick)
        >>> await emitter.emit('tick', tick_data)
    """

    def __init__(self) -> None:
        """Initialize event emitter."""
        self._listeners: dict[str, list[Callable]] = defaultdict(list)
        self._once_listeners: dict[str, list[Callable]] = defaultdict(list)

    def on(self, event: str, callback: Callable) -> None:
        """Register a callback for an event.

        Args:
            event: Event name (e.g., 'tick', 'error', 'connected')
            callback: Function to call when event is emitted

        Example:
            >>> emitter.on('tick', lambda tick: print(tick))
        """
        if not callable(callback):
            raise TypeError(f"Callback must be callable, got {type(callback)}")
        self._listeners[event].append(callback)

    def once(self, event: str, callback: Callable) -> None:
        """Register a one-time callback for an event.

        The callback will be removed after it's called once.

        Args:
            event: Event name
            callback: Function to call once when event is emitted

        Example:
            >>> emitter.once('connected', lambda: print("Connected!"))
        """
        if not callable(callback):
            raise TypeError(f"Callback must be callable, got {type(callback)}")
        self._once_listeners[event].append(callback)

    def off(self, event: str, callback: Optional[Callable] = None) -> None:
        """Remove event callback(s).

        Args:
            event: Event name
            callback: Specific callback to remove, or None to remove all

        Example:
            >>> # Remove specific callback
            >>> emitter.off('tick', my_callback)
            >>> # Remove all callbacks for event
            >>> emitter.off('tick')
        """
        if callback is None:
            # Remove all callbacks for event
            self._listeners[event].clear()
            self._once_listeners[event].clear()
        else:
            # Remove specific callback
            if callback in self._listeners[event]:
                self._listeners[event].remove(callback)
            if callback in self._once_listeners[event]:
                self._once_listeners[event].remove(callback)

    async def emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        """Trigger all callbacks for an event.

        Executes all registered callbacks for the event with the given arguments.
        Async callbacks are awaited, sync callbacks are called directly.

        Args:
            event: Event name to emit
            *args: Positional arguments to pass to callbacks
            **kwargs: Keyword arguments to pass to callbacks
        """
        # Get all callbacks for this event
        callbacks = self._listeners.get(event, [])[:]
        once_callbacks = self._once_listeners.get(event, [])[:]

        # Clear once callbacks before execution
        self._once_listeners[event].clear()

        # Execute all callbacks
        for callback in callbacks + once_callbacks:
            try:
                result = callback(*args, **kwargs)
                # If callback is async coroutine, await it
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Error in event callback for '{event}': {e}")

    def listener_count(self, event: str) -> int:
        """Get the number of listeners for an event.

        Args:
            event: Event name

        Returns:
            Number of registered callbacks
        """
        return len(self._listeners.get(event, [])) + len(self._once_listeners.get(event, []))

    def remove_all_listeners(self, event: Optional[str] = None) -> None:
        """Remove all listeners.

        Args:
            event: Specific event to clear, or None to clear all events
        """
        if event is None:
            self._listeners.clear()
            self._once_listeners.clear()
        else:
            self._listeners[event].clear()
            self._once_listeners[event].clear()

    def event_names(self) -> list[str]:
        """Get list of all registered event names.

        Returns:
            List of event names that have listeners
        """
        events = set(self._listeners.keys()) | set(self._once_listeners.keys())
        return list(events)

    def __repr__(self) -> str:
        """String representation of emitter."""
        total_listeners = sum(
            len(callbacks) + len(once_callbacks)
            for callbacks, once_callbacks in zip(
                self._listeners.values(), self._once_listeners.values()
            )
        )
        return f"EventEmitter(events={len(self.event_names())}, listeners={total_listeners})"
