"""
Unit tests for EventManager class.
"""

import pytest
from unittest.mock import Mock, MagicMock

from codexify.events import EventManager, PROJECT_LOADED, FILES_UPDATED, STATUS_CHANGED


class TestEventManager:
    """Test cases for EventManager class."""
    
    def test_initialization(self):
        """Test EventManager initialization."""
        manager = EventManager()
        
        assert manager._subscribers is not None
        assert len(manager._subscribers) == 0
    
    def test_subscribe_to_event(self):
        """Test subscribing to a specific event type."""
        manager = EventManager()
        callback = Mock()
        
        manager.subscribe("test_event", callback)
        
        assert "test_event" in manager._subscribers
        assert callback in manager._subscribers["test_event"]
        assert len(manager._subscribers["test_event"]) == 1
    
    def test_subscribe_to_multiple_events(self):
        """Test subscribing to multiple event types."""
        manager = EventManager()
        callback1 = Mock()
        callback2 = Mock()
        
        manager.subscribe("event1", callback1)
        manager.subscribe("event2", callback2)
        
        assert "event1" in manager._subscribers
        assert "event2" in manager._subscribers
        assert callback1 in manager._subscribers["event1"]
        assert callback2 in manager._subscribers["event2"]
    
    def test_multiple_subscribers_to_same_event(self):
        """Test multiple subscribers to the same event type."""
        manager = EventManager()
        callback1 = Mock()
        callback2 = Mock()
        callback3 = Mock()
        
        manager.subscribe("test_event", callback1)
        manager.subscribe("test_event", callback2)
        manager.subscribe("test_event", callback3)
        
        assert len(manager._subscribers["test_event"]) == 3
        assert callback1 in manager._subscribers["test_event"]
        assert callback2 in manager._subscribers["test_event"]
        assert callback3 in manager._subscribers["test_event"]
    
    def test_subscribe_duplicate_callback(self):
        """Test that duplicate callbacks are not added."""
        manager = EventManager()
        callback = Mock()
        
        # Subscribe the same callback multiple times
        manager.subscribe("test_event", callback)
        manager.subscribe("test_event", callback)
        manager.subscribe("test_event", callback)
        
        # Should only be added once
        assert len(manager._subscribers["test_event"]) == 1
        assert callback in manager._subscribers["test_event"]
    
    def test_post_event_to_subscribers(self):
        """Test posting an event to subscribed callbacks."""
        manager = EventManager()
        callback1 = Mock()
        callback2 = Mock()
        
        manager.subscribe("test_event", callback1)
        manager.subscribe("test_event", callback2)
        
        event_data = {"message": "Hello World"}
        manager.post("test_event", event_data)
        
        # Verify callbacks were called with the event data
        callback1.assert_called_once_with(event_data)
        callback2.assert_called_once_with(event_data)
    
    def test_post_event_to_no_subscribers(self):
        """Test posting an event when no subscribers exist."""
        manager = EventManager()
        
        # Should not raise an error
        manager.post("test_event", {"data": "value"})
    
    def test_post_event_to_different_event_type(self):
        """Test that events are only sent to subscribers of the correct type."""
        manager = EventManager()
        callback1 = Mock()
        callback2 = Mock()
        
        manager.subscribe("event1", callback1)
        manager.subscribe("event2", callback2)
        
        manager.post("event1", {"data": "value1"})
        
        callback1.assert_called_once_with({"data": "value1"})
        callback2.assert_not_called()
    
    def test_callback_error_handling(self):
        """Test that errors in callbacks don't break other callbacks."""
        manager = EventManager()
        callback1 = Mock(side_effect=Exception("Test error"))
        callback2 = Mock()
        
        manager.subscribe("test_event", callback1)
        manager.subscribe("test_event", callback2)
        
        # Post event - callback1 should fail but callback2 should still execute
        manager.post("test_event", {"data": "test"})
        
        # Verify both callbacks were called
        callback1.assert_called_once_with({"data": "test"})
        callback2.assert_called_once_with({"data": "test"})
    
    def test_event_constants(self):
        """Test that event type constants are defined."""
        assert PROJECT_LOADED == "PROJECT_LOADED"
        assert FILES_UPDATED == "FILES_UPDATED"
        assert STATUS_CHANGED == "STATUS_CHANGED"
        assert ANALYSIS_COMPLETE == "ANALYSIS_COMPLETE"
        assert "COLLECTION_COMPLETE" in dir()
        assert "SETTINGS_CHANGED" in dir()
    
    def test_subscriber_persistence(self):
        """Test that subscribers persist across multiple posts."""
        manager = EventManager()
        callback = Mock()
        
        manager.subscribe("test_event", callback)
        
        # Post multiple events
        for i in range(5):
            manager.post("test_event", {"count": i})
        
        # Verify callback was called for each post
        assert callback.call_count == 5
        
        # Verify all calls received correct data
        for i in range(5):
            call_args = callback.call_args_list[i][0][0]
            assert call_args["count"] == i
    
    def test_complex_event_data(self):
        """Test posting events with complex data structures."""
        manager = EventManager()
        received_data = None
        
        def data_collector(data):
            nonlocal received_data
            received_data = data
        
        manager.subscribe("test_event", data_collector)
        
        complex_data = {
            "string": "Hello",
            "number": 42,
            "boolean": True,
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "none": None
        }
        
        manager.post("test_event", complex_data)
        
        assert received_data == complex_data
        assert received_data["string"] == "Hello"
        assert received_data["number"] == 42
        assert received_data["boolean"] is True
        assert received_data["list"] == [1, 2, 3]
        assert received_data["dict"]["nested"] == "value"
        assert received_data["none"] is None
    
    def test_empty_event_data(self):
        """Test posting events with no data."""
        manager = EventManager()
        callback = Mock()
        
        manager.subscribe("test_event", callback)
        
        # Post event with no data
        manager.post("test_event")
        
        # Verify callback was called with None
        callback.assert_called_once_with(None)
    
    def test_multiple_event_types(self):
        """Test handling multiple different event types."""
        manager = EventManager()
        callback = Mock()
        
        # Subscribe to multiple event types
        manager.subscribe("event1", callback)
        manager.subscribe("event2", callback)
        manager.subscribe("event3", callback)
        
        # Post different events
        manager.post("event1", "data1")
        manager.post("event2", "data2")
        manager.post("event3", "data3")
        
        # Verify callback was called for each event type
        assert callback.call_count == 3
        
        # Verify correct data was passed
        call_args = callback.call_args_list
        assert call_args[0][0][0] == "data1"
        assert call_args[1][0][0] == "data2"
        assert call_args[2][0][0] == "data3"
    
    def test_subscriber_removal_during_post(self):
        """Test that removing subscribers during post doesn't break the system."""
        manager = EventManager()
        callback1 = Mock()
        callback2 = Mock()
        
        def callback_that_unsubscribes(data):
            # This callback removes itself during execution
            manager._subscribers["test_event"].remove(callback_that_unsubscribes)
        
        manager.subscribe("test_event", callback1)
        manager.subscribe("test_event", callback_that_unsubscribes)
        manager.subscribe("test_event", callback2)
        
        # Post event - callback_that_unsubscribes should remove itself
        manager.post("test_event", "test_data")
        
        # Verify callbacks were called
        callback1.assert_called_once_with("test_data")
        callback2.assert_called_once_with("test_data")
        
        # Verify callback_that_unsubscribes was removed
        assert callback_that_unsubscribes not in manager._subscribers["test_event"]
    
    def test_event_manager_independence(self):
        """Test that multiple EventManager instances are independent."""
        manager1 = EventManager()
        manager2 = EventManager()
        callback = Mock()
        
        # Subscribe to both managers
        manager1.subscribe("test_event", callback)
        manager2.subscribe("test_event", callback)
        
        # Post event to manager1 only
        manager1.post("test_event", "data1")
        
        # Verify callback was called once (only for manager1)
        assert callback.call_count == 1
        callback.assert_called_once_with("data1")
        
        # Post event to manager2
        manager2.post("test_event", "data2")
        
        # Verify callback was called twice now
        assert callback.call_count == 2
        assert callback.call_args_list[1][0][0] == "data2"
