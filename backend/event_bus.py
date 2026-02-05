
from typing import Callable, Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass
import logging

logger = logging.getLogger("event_bus")

class EventType(str, Enum):
    PAPER_ADDED = "paper_added"
    USER_FEEDBACK = "user_feedback"
    RESEARCH_COMPLETED = "research_completed"

@dataclass
class Event:
    type: EventType
    payload: Any
    source: str = "system"

_subscribers: Dict[EventType, List[Callable[[Event], None]]] = {}

def subscribe(event_type: EventType, handler: Callable[[Event], None]):
    """
    Subscribe a handler function to an event type.
    """
    if event_type not in _subscribers:
        _subscribers[event_type] = []
    _subscribers[event_type].append(handler)
    logger.info(f"Subscribed {handler.__name__} to {event_type}")

def emit(event_type: EventType, payload: Any, source: str = "system"):
    """
    Broadcast an event to all subscribers.
    Currently synchronous for simplicity.
    """
    event = Event(type=event_type, payload=payload, source=source)
    
    if event_type in _subscribers:
        handlers = _subscribers[event_type]
        logger.info(f"Emitting {event_type} to {len(handlers)} handlers")
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in handler {handler.__name__}: {e}")
    else:
        logger.debug(f"No subscribers for {event_type}")

def clear_subscribers():
    """For testing purposes"""
    _subscribers.clear()
