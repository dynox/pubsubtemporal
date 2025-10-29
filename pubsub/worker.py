from __future__ import annotations

import asyncio
import importlib
import logging

from temporalio.client import Client
from temporalio.worker import Worker

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
    # Eagerly import submodules so decorators execute and register
    import pkgutil

    for m in pkgutil.walk_packages(pkg.__path__, prefix=f"{package_name}."):
        try:
            importlib.import_module(m.name)
        except Exception:
            # Skip modules that fail to import to avoid crashing worker startup
            pass


async def run_worker() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    settings = TemporalSettings()

    # Discover workflows and activities by importing their packages
    _import_package_modules("pubsub.workflows")
    _import_package_modules("pubsub.activities")

    client = await Client.connect(settings.address, namespace=settings.namespace)
    workflows = list(get_workflows())
    activities = list(get_activities())

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
