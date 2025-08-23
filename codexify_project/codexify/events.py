from collections import defaultdict
from typing import Callable, Any, DefaultDict, List

class EventManager:
    """
    Implements the Observer pattern for event handling.
    Allows different parts of the application to communicate without being directly coupled.
    """
    def __init__(self):
        self._subscribers: DefaultDict[str, List[Callable]] = defaultdict(list)

    def subscribe(self, event_type: str, callback: Callable):
        """
        Subscribes a callback function to a specific event type.
        """
        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)

    def post(self, event_type: str, data: Any = None):
        """
        Notifies all subscribers of a given event type.
        """
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"Error in event callback for {event_type}: {e}")

# Define event type constants for consistency
PROJECT_LOADED = "PROJECT_LOADED"
FILES_UPDATED = "FILES_UPDATED"
STATUS_CHANGED = "STATUS_CHANGED"
ANALYSIS_COMPLETE = "ANALYSIS_COMPLETE"
COLLECTION_COMPLETE = "COLLECTION_COMPLETE"
SETTINGS_CHANGED = "SETTINGS_CHANGED"
