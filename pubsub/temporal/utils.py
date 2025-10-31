from __future__ import annotations

import importlib
import inspect
import logging
import pkgutil
from typing import Callable, Iterable, List, Type

log = logging.getLogger(__name__)


def register_workflow(cls: Type) -> Type:
    cls.__object_type__ = "workflow"
    return cls


def register_activity(cls: Type) -> Type:
    cls.__object_type__ = "activity"
    return cls


def subscribe(event_type: str) -> Callable[[Type], Type]:
    def decorator(cls: Type) -> Type:
        cls.__subscribed_on__ = event_type
        cls.__object_type__ = "workflow"
        return cls

    return decorator


def discover_objects(package_name: str, object_type: str) -> List[Type]:
    seen: set[Type] = set()
    log.info(f"Discovering {object_type}s in {package_name}")

    def scan(pkg_name: str) -> None:
        module = importlib.import_module(pkg_name)
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if getattr(obj, "__object_type__", None) == object_type:
                seen.add(obj)

        if path := getattr(module, "__path__", None):
            for finder, name, is_pkg in pkgutil.iter_modules(path):
                full_name = f"{pkg_name}.{name}"
                scan(full_name)

    scan(package_name)
    return sorted(seen, key=lambda x: x.__name__)


def get_workflows(package_name: str = "pubsub") -> Iterable[Type]:
    return discover_objects(package_name, "workflow")


def get_activities(package_name: str = "pubsub") -> Iterable[Type]:
    return discover_objects(package_name, "activity")
