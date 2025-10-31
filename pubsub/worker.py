from __future__ import annotations  # noqa: I001

import asyncio
import importlib
import logging
import pkgutil

from temporalio.client import Client
from temporalio.worker import Worker

from temporalio.contrib.pydantic import pydantic_data_converter
from pubsub.importer import import_package_modules
from pubsub.temporal.registry import get_activities, get_workflows
from pubsub.temporal.settings import TemporalSettings

log = logging.getLogger(__name__)


async def run_worker() -> None:

    settings = TemporalSettings()

    # Discover workflows and activities by importing their packages
    import_package_modules("pubsub")

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
        log.info("Worker started")
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(run_worker())
