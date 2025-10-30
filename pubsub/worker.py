from __future__ import annotations  # noqa: I001

import asyncio
import importlib
import logging
import pkgutil

from temporalio.client import Client
from temporalio.worker import Worker

from temporalio.contrib.pydantic import pydantic_data_converter
from pubsub.temporal.registry import get_activities, get_workflows
from pubsub.temporal.settings import TemporalSettings

log = logging.getLogger(__name__)


def _import_package_modules(package_name: str) -> None:
    try:
        pkg = importlib.import_module(package_name)
    except Exception:
        return
    pkg_path = getattr(pkg, "__path__", None)
    if not pkg_path:
        return

    visited: set[str] = set()
    to_process: list[str] = [package_name]

    while to_process:
        current = to_process.pop(0)
        if current in visited:
            continue
        visited.add(current)

        try:
            current_pkg = importlib.import_module(current)
            current_pkg_path = getattr(current_pkg, "__path__", None)
            if current_pkg_path:
                for finder, name, is_pkg in pkgutil.iter_modules(current_pkg_path):
                    full_name = f"{current}.{name}"
                    if full_name not in visited:
                        try:
                            importlib.import_module(full_name)
                            if is_pkg:
                                to_process.append(full_name)
                        except Exception:
                            pass
        except Exception:
            pass


async def run_worker() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    settings = TemporalSettings()

    # Discover workflows and activities by importing their packages
    _import_package_modules("pubsub")

    workflows = list(get_workflows())
    activities = list(get_activities())
    for workflow in workflows:
        log.info(f"Workflow: {workflow.__name__}")
    for activity in activities:
        log.info(f"Activity: {activity.__name__}")
    client = await Client.connect(
        settings.address,
        namespace=settings.namespace,
        data_converter=pydantic_data_converter,
    )
    async with Worker(
        client,
        task_queue=settings.task_queue,
        workflows=workflows,
        activities=activities,
    ):
        log.info("Worker started aaa")
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(run_worker())
