from __future__ import annotations  # noqa: I001

import asyncio
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from temporalio.contrib.pydantic import pydantic_data_converter
from pubsub.temporal.settings import TemporalSettings
from pubsub.temporal.utils import get_activities, get_workflows

log = logging.getLogger(__name__)


async def run_worker() -> None:
    settings = TemporalSettings()

    workflows = list(get_workflows("pubsub"))
    activities = list(get_activities("pubsub"))
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
