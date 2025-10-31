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


async def run_worker() -> None:
    settings = TemporalSettings()

    workflow_classes = list(get_workflows("pubsub"))
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
    async with Worker(
        client,
        task_queue=settings.task_queue,
        workflows=workflow_classes,
        activities=[activity_cls(injector) for activity_cls in activities_classes],
    ):
        log.info("Worker started")
        await asyncio.Event().wait()
