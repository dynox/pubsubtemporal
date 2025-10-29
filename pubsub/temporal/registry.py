from __future__ import annotations

from typing import Callable, Iterable, List, Type

_registered_workflows: List[Type] = []
_registered_activities: List[Callable] = []


def workflow(cls: Type) -> Type:
    if cls not in _registered_workflows:
        _registered_workflows.append(cls)
    return cls


def activity(fn: Callable) -> Callable:
    if fn not in _registered_activities:
        _registered_activities.append(fn)
    return fn


def get_workflows() -> Iterable[Type]:
    return tuple(_registered_workflows)


def get_activities() -> Iterable[Callable]:
    return tuple(_registered_activities)
