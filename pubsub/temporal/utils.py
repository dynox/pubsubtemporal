from __future__ import annotations

import importlib
import pkgutil
from collections import defaultdict
from typing import Callable, Dict, Iterable, List, Tuple, Type

_registered_workflows: List[Type] = []
_registered_activities: List[Callable] = []
_registry_instance: Registry | None = None


class Registry:
    def __init__(self) -> None:
        self._event_subscribers: Dict[str, List[Type]] = defaultdict(list)

    def set_subscribers(self, event_type: str, workflow: Type) -> None:
        self._event_subscribers[event_type].append(workflow)

    def get_subscribers(self, event_type: str) -> Tuple[Type, ...]:
        return tuple(self._event_subscribers.get(event_type, ()))

    def get_all_subscriptions(self) -> Dict[str, List[Type]]:
        return {k: list(v) for k, v in self._event_subscribers.items()}

    @classmethod
    def create(cls, workflows: Iterable[Type]) -> Registry:
        registry = cls()
        for workflow in workflows:
            if hasattr(workflow, "__subscribes__"):
                registry.set_subscribers(workflow.__subscribes__, workflow)
        return registry


def _get_registry() -> Registry:
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = Registry.create(_registered_workflows)
    return _registry_instance


def register_workflow(cls: Type) -> Type:
    if cls not in _registered_workflows:
        _registered_workflows.append(cls)
        global _registry_instance
        _registry_instance = None
    return cls


def register_activity(fn: Callable) -> Callable:
    if fn not in _registered_activities:
        _registered_activities.append(fn)
    return fn


def subscribe(event_type: str) -> Callable[[Type], Type]:
    def decorator(cls: Type) -> Type:
        cls.__subscribes__ = event_type
        register_workflow(cls)
        return cls

    return decorator


def get_workflows() -> Iterable[Type]:
    return _registered_workflows


def get_activities() -> Iterable[Callable]:
    return _registered_activities


def get_subscribers(event_type: str) -> Tuple[Type, ...]:
    return _get_registry().get_subscribers(event_type)


def get_all_workflows() -> Dict[str, Type]:
    portion: Dict[str, Type] = {}
    for workflow in _registered_workflows:
        portion[workflow.__name__] = workflow
    return portion


def get_all_subscriptions() -> Dict[str, List[Type]]:
    return _get_registry().get_all_subscriptions()


def import_package_modules(package_name: str) -> None:
    try:
        root = importlib.import_module(package_name)
    except Exception:
        return

    root_path = getattr(root, "__path__", None)
    if not root_path:
        return

    for finder, name, is_pkg in pkgutil.iter_modules(root_path):
        full_name = f"{package_name}.{name}"
        try:
            importlib.import_module(full_name)

            if is_pkg:
                import_package_modules(full_name)
        except Exception:
            pass
