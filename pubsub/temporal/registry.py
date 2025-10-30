from __future__ import annotations

from typing import Callable, Dict, Iterable, List, Mapping, Tuple, Type

global _registered_workflows

_registered_workflows: dict[str, Type] = {}
_registered_activities: List[Callable] = []
_event_subscribers: Dict[str, List[Type]] = {}


def register_workflow(cls: Type) -> Type:
    if cls.__name__ not in _registered_workflows:
        _registered_workflows[cls.__name__] = cls
    return cls


def regsiter_activity(fn: Callable) -> Callable:
    if fn not in _registered_activities:
        _registered_activities.append(fn)
    return fn


def get_workflows() -> Iterable[Type]:
    return tuple(_registered_workflows.values())


def get_activities() -> Iterable[Callable]:
    return tuple(_registered_activities)


def subscribe(event_type: str) -> Callable[[Type], Type]:
    def decorator(cls: Type) -> Type:
        if event_type not in _event_subscribers:
            _event_subscribers[event_type] = []
        if cls not in _event_subscribers[event_type]:
            _event_subscribers[event_type].append(cls)
        if cls.__name__ not in _registered_workflows:
            _registered_workflows[cls.__name__] = cls
        return cls

    return decorator


def get_subscribers(event_type: str) -> Tuple[Type, ...]:
    return tuple(_event_subscribers.get(event_type, ()))


def get_workflow_by_name(name: str):
    return _registered_workflows.get(name, None)


def get_all_workflows() -> dict[str, Type]:
    return _registered_workflows


def get_all_subscriptions() -> Mapping[str, Tuple[Type, ...]]:
    return {k: tuple(v) for k, v in _event_subscribers.items()}
