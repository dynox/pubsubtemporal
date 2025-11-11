from __future__ import annotations  # noqa: I001

import asyncio
import logging

from pydio.injector import Injector
from temporalio.client import Client
from temporalio.worker import Worker

from temporalio.contrib.pydantic import pydantic_data_converter
from pubsub.temporal.settings import TemporalSettings
from pubsub.temporal.utils import get_activities
from pubsub.di import provider
from pubsub.domain_b.consumers import ConsumerB

log = logging.getLogger(__name__)


async def run_worker() -> None:
    settings = TemporalSettings()

    # Only register ConsumerB for this worker
    workflow_classes = [ConsumerB]
    activities_classes = list(get_activities("pubsub"))

    for workflow in workflow_classes:
        log.info(f"Workflow: {workflow.__name__}")
    for activity in activities_classes:
        log.info(f"Activity: {activity.__name__}")

    injector = Injector(provider)

    client = await Client.connect(
        settings.address,
        namespace=settings.namespace,
        data_converter=pydantic_data_converter,
    )

    # Use secondary task queue from settings
    task_queue = settings.task_queue_secondary
    log.info(f"Starting secondary worker on task queue: {task_queue}")

    async with Worker(
        client,
        task_queue=task_queue,
        workflows=workflow_classes,
        activities=[activity_cls(injector).run for activity_cls in activities_classes],
    ):
        log.info(f"Secondary worker started on task queue: {task_queue}")
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(run_worker())
