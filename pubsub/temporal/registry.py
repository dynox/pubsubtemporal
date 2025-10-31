from __future__ import annotations

from collections import defaultdict
from typing import Callable, Dict, Iterable, List, Tuple, Type

_registered_workflows: List[Type] = []
_registered_activities: List[Callable] = []


class Registry:
    def __init__(self) -> None:
        self._event_subscribers: Dict[str, defaultdict(list)] = defaultdict(list)

    def set_subscribers(self, event_type: str, workflow: Type) -> None:
        self._event_subscribers[event_type].append(workflow)

    def get_subscribers(self, event_type: str) -> Tuple[Type, ...]:
        return tuple(self._event_subscribers.get(event_type, ()))

    @classmethod
    def create(cls, workflows: Iterable[Type]) -> Registry:
        registry = cls()
        for workflow in workflows:
            if hasattr(workflow, "__subscribes__"):
                registry.set_subscribers(workflow.__subscribes__, workflow)
        return registry


def register_workflow(cls: Type) -> Type:
    if cls not in _registered_workflows:
        _registered_workflows.append(cls)
    return cls


def register_activity(fn: Callable) -> Callable:
    if fn.__name__ not in _registered_activities:
        _registered_activities.append(fn)
    return fn


def subscribe(event_type: str) -> Callable[[Type], Type]:
    def decorator(cls: Type) -> Type:
        cls.__subscribes__ = event_type
        register_workflow(cls)
        return cls

    return decorator
