from __future__ import annotations

import logging
from datetime import timedelta

from temporalio import workflow

from pubsub.event_dispatchers import (
    DispatchEventWithSignal,
    EventDispatcherWorkflow,
    SpawnEventSubscribers,
)
from pubsub.events import EventDispatchInput
from pubsub.temporal.utils import register_workflow

log = logging.getLogger(__name__)


@register_workflow
@workflow.defn
class ProducerActivity:
    @workflow.run
    async def run(self, args: EventDispatchInput) -> None:
        log.info(f"ProducerActivity dispatching event: {args.event_type}")
        await workflow.execute_activity(
            SpawnEventSubscribers,
            args=(args,),
            start_to_close_timeout=timedelta(seconds=60),
        )


@register_workflow
@workflow.defn
class ProducerWorkflow:
    @workflow.run
    async def run(self, args: EventDispatchInput) -> None:
        log.info(f"ProducerWorkflow dispatching event: {args.event_type}")
        handle = await workflow.start_child_workflow(
            EventDispatcherWorkflow.run,
            args,
            id=f"event-dispatcher-{args.event_type}-{workflow.info().workflow_id}",
        )
        await handle


@register_workflow
@workflow.defn
class ProducerSignal:
    @workflow.run
    async def run(self, args: EventDispatchInput) -> None:
        log.info(f"ProducerSignal dispatching event: {args.event_type}")
        await workflow.execute_activity(
            DispatchEventWithSignal,
            args=(args,),
            start_to_close_timeout=timedelta(seconds=60),
        )
