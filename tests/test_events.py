"""Tests for EventEmitter.

Unit tests for the callback-based event system.
"""

import pytest
import asyncio
from datetime import datetime

from cbsc_strategy_sdk.data.events import EventEmitter


class TestEventEmitter:
    """Test EventEmitter functionality."""

    def test_init(self) -> None:
        """Test EventEmitter initialization."""
        emitter = EventEmitter()
        assert emitter.event_names() == []
        assert emitter.listener_count('test') == 0

    def test_on_callback(self) -> None:
        """Test registering a callback with on()."""
        emitter = EventEmitter()
        callback = lambda x: x * 2

        emitter.on('test', callback)

        assert emitter.listener_count('test') == 1
        assert 'test' in emitter.event_names()

    def test_once_callback(self) -> None:
        """Test registering a one-time callback with once()."""
        emitter = EventEmitter()
        callback = lambda: 'result'

        emitter.once('test', callback)

        assert emitter.listener_count('test') == 1

    def test_off_specific_callback(self) -> None:
        """Test removing a specific callback with off()."""
        emitter = EventEmitter()
        callback1 = lambda x: x
        callback2 = lambda x: x * 2

        emitter.on('test', callback1)
        emitter.on('test', callback2)
        assert emitter.listener_count('test') == 2

        emitter.off('test', callback1)
        assert emitter.listener_count('test') == 1

    def test_off_all_callbacks(self) -> None:
        """Test removing all callbacks with off()."""
        emitter = EventEmitter()
        callback1 = lambda x: x
        callback2 = lambda x: x * 2

        emitter.on('test', callback1)
        emitter.on('test', callback2)
        assert emitter.listener_count('test') == 2

        emitter.off('test')
        assert emitter.listener_count('test') == 0

    def test_emit_sync_callback(self) -> None:
        """Test emitting event with synchronous callback."""
        emitter = EventEmitter()
        results = []

        def callback(value):
            results.append(value)

        emitter.on('test', callback)
        asyncio.run(emitter.emit('test', 42))

        assert results == [42]

    def test_emit_async_callback(self) -> None:
        """Test emitting event with async callback."""
        emitter = EventEmitter()
        results = []

        async def callback(value):
            await asyncio.sleep(0.01)
            results.append(value)

        emitter.on('test', callback)
        asyncio.run(emitter.emit('test', 42))

        assert results == [42]

    def test_emit_multiple_callbacks(self) -> None:
        """Test emitting event to multiple callbacks."""
        emitter = EventEmitter()
        results = []

        emitter.on('test', lambda x: results.append(f'cb1:{x}'))
        emitter.on('test', lambda x: results.append(f'cb2:{x}'))
        emitter.on('test', lambda x: results.append(f'cb3:{x}'))

        asyncio.run(emitter.emit('test', 42))

        assert results == ['cb1:42', 'cb2:42', 'cb3:42']

    def test_once_removes_after_call(self) -> None:
        """Test that once callbacks are removed after being called."""
        emitter = EventEmitter()
        results = []

        callback = lambda: results.append('called')
        emitter.once('test', callback)

        asyncio.run(emitter.emit('test'))
        assert results == ['called']
        assert emitter.listener_count('test') == 0

    def test_emit_with_multiple_args(self) -> None:
        """Test emitting event with multiple arguments."""
        emitter = EventEmitter()
        results = []

        emitter.on('test', lambda a, b, c: results.append((a, b, c)))

        asyncio.run(emitter.emit('test', 1, 2, 3))

        assert results == [(1, 2, 3)]

    def test_emit_with_kwargs(self) -> None:
        """Test emitting event with keyword arguments."""
        emitter = EventEmitter()
        results = []

        emitter.on('test', lambda **kwargs: results.append(kwargs))

        asyncio.run(emitter.emit('test', value=42, name='test'))

        assert results == [{'value': 42, 'name': 'test'}]

    def test_listener_count(self) -> None:
        """Test getting listener count for event."""
        emitter = EventEmitter()

        assert emitter.listener_count('nonexistent') == 0

        emitter.on('test', lambda: None)
        emitter.on('test', lambda: None)
        emitter.once('test', lambda: None)

        assert emitter.listener_count('test') == 3

    def test_event_names(self) -> None:
        """Test getting list of event names."""
        emitter = EventEmitter()

        emitter.on('event1', lambda: None)
        emitter.on('event2', lambda: None)
        emitter.on('event3', lambda: None)

        events = set(emitter.event_names())
        assert events == {'event1', 'event2', 'event3'}

    def test_remove_all_listeners_specific_event(self) -> None:
        """Test removing all listeners for specific event."""
        emitter = EventEmitter()

        emitter.on('event1', lambda: None)
        emitter.on('event1', lambda: None)
        emitter.on('event2', lambda: None)

        emitter.remove_all_listeners('event1')

        assert emitter.listener_count('event1') == 0
        assert emitter.listener_count('event2') == 1

    def test_remove_all_listeners_all_events(self) -> None:
        """Test removing all listeners for all events."""
        emitter = EventEmitter()

        emitter.on('event1', lambda: None)
        emitter.on('event2', lambda: None)
        emitter.on('event3', lambda: None)

        emitter.remove_all_listeners()

        assert emitter.listener_count('event1') == 0
        assert emitter.listener_count('event2') == 0
        assert emitter.listener_count('event3') == 0

    def test_callback_exception_handling(self) -> None:
        """Test that exceptions in callbacks don't stop other callbacks."""
        emitter = EventEmitter()
        results = []

        def bad_callback():
            raise ValueError("Error!")

        def good_callback():
            results.append('success')

        emitter.on('test', bad_callback)
        emitter.on('test', good_callback)

        # Should not raise exception
        asyncio.run(emitter.emit('test'))

        # Good callback should still be called
        assert results == ['success']

    def test_non_callable_raises(self) -> None:
        """Test that non-callable raises TypeError."""
        emitter = EventEmitter()

        with pytest.raises(TypeError):
            emitter.on('test', 'not a function')

    def test_repr(self) -> None:
        """Test string representation."""
        emitter = EventEmitter()

        emitter.on('event1', lambda: None)
        emitter.on('event1', lambda: None)
        emitter.on('event2', lambda: None)

        repr_str = repr(emitter)
        assert 'EventEmitter' in repr_str
        assert 'events=2' in repr_str
        assert 'listeners=3' in repr_str


class TestEventEmitterIntegration:
    """Integration tests for EventEmitter usage patterns."""

    @pytest.mark.asyncio
    async def test_event_driven_pattern(self) -> None:
        """Test typical event-driven usage pattern."""
        emitter = EventEmitter()
        state = {'connected': False, 'ticks': []}

        def on_connected():
            state['connected'] = True

        def on_tick(tick):
            state['ticks'].append(tick)

        emitter.on('connected', on_connected)
        emitter.on('tick', on_tick)

        # Simulate connection
        await emitter.emit('connected')
        assert state['connected'] is True

        # Simulate ticks
        await emitter.emit('tick', {'symbol': 'AAPL', 'price': 100})
        await emitter.emit('tick', {'symbol': 'AAPL', 'price': 101})

        assert len(state['ticks']) == 2

    @pytest.mark.asyncio
    async def test_error_handling_pattern(self) -> None:
        """Test error handling with event emitter."""
        emitter = EventEmitter()
        errors = []

        def on_error(error):
            errors.append(error)

        emitter.on('error', on_error)

        # Simulate error
        await emitter.emit('error', ValueError("Connection failed"))

        assert len(errors) == 1
        assert isinstance(errors[0], ValueError)

    @pytest.mark.asyncio
    async def test_once_for_initialization(self) -> None:
        """Test using once for one-time initialization."""
        emitter = EventEmitter()
        initialized = []

        emitter.once('init', lambda: initialized.append(True))

        # First emit calls callback
        await emitter.emit('init')
        assert initialized == [True]

        # Second emit doesn't call callback
        await emitter.emit('init')
        assert initialized == [True]  # Still only one
