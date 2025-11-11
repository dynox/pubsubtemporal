from __future__ import annotations  # noqa: I001

import asyncio
import logging

from pydio.injector import Injector
from temporalio.client import Client
from temporalio.worker import Worker

from temporalio.contrib.pydantic import pydantic_data_converter
from pubsub.temporal.settings import TemporalSettings
from pubsub.temporal.utils import get_activities, get_workflows
from pubsub.di import provider

log = logging.getLogger(__name__)


async def run_worker_with_packages(
    workflow_packages: list[str],
    activity_packages: list[str],
    task_queue: str,
) -> None:
    """
    Run a Temporal worker with workflows and activities from specified packages.

    Args:
        workflow_packages: List of package paths to load workflows from
        activity_packages: List of package paths to load activities from
        task_queue: Task queue name for this worker
    """
    settings = TemporalSettings()

    # Load workflows and activities from specified packages
    workflow_classes = []
    for package in workflow_packages:
        workflow_classes.extend(get_workflows(package))

    activities_classes = []
    for package in activity_packages:
        activities_classes.extend(get_activities(package))

    # Deduplicate workflows and activities
    # (in case they're discovered from multiple packages)
    workflow_classes = list(dict.fromkeys(workflow_classes))
    activities_classes = list(dict.fromkeys(activities_classes))

    log.info(
        f"Worker loading from packages: "
        f"workflows={workflow_packages}, "
        f"activities={activity_packages}"
    )
    log.info(f"Worker task queue: {task_queue}")

    log.info(f"Found {len(workflow_classes)} workflow(s):")
    for workflow in workflow_classes:
        log.info(f"  - {workflow.__name__} (from {workflow.__module__})")

    log.info(f"Found {len(activities_classes)} activity/activities:")
    for activity in activities_classes:
        log.info(f"  - {activity.__name__} (from {activity.__module__})")

    injector = Injector(provider)

    client = await Client.connect(
        settings.address,
        namespace=settings.namespace,
        data_converter=pydantic_data_converter,
    )

    async with Worker(
        client,
        task_queue=task_queue,
        workflows=workflow_classes,
        activities=[activity_cls(injector).run for activity_cls in activities_classes],
    ):
        log.info(f"Worker started on task queue: {task_queue}")
        await asyncio.Event().wait()


async def run_worker() -> None:
    """Primary worker - loads domain_a and common packages."""
    settings = TemporalSettings()
    await run_worker_with_packages(
        workflow_packages=["pubsub.domain_a", "pubsub.common"],
        activity_packages=["pubsub.domain_a", "pubsub.common"],
        task_queue=settings.task_queue,
    )


if __name__ == "__main__":
    asyncio.run(run_worker())
