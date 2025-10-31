from __future__ import annotations

import logging
from datetime import timedelta

from temporalio import workflow

from pubsub.dispatchers import (
    DispatchWithSignalAndStart,
    DispatchWithTemporalClient,
)
from pubsub.events import EventDispatchInput
from pubsub.temporal.utils import register_workflow

log = logging.getLogger(__name__)


@register_workflow
@workflow.defn
class ProducerActivity:
    @workflow.run
    async def run(self, args: EventDispatchInput) -> None:
        log.info(
            f"ProducerActivity dispatching event: {args.event_type} (id: {args.id})"
        )
        await workflow.execute_activity(
            DispatchWithTemporalClient.run,
            args=(args,),
            start_to_close_timeout=timedelta(seconds=60),
        )


@register_workflow
@workflow.defn
class ProducerActivityRepeated:
    @workflow.run
    async def run(self, args: EventDispatchInput) -> None:
        log.info(
            f"ProducerActivityRepeated dispatching event twice: "
            f"{args.event_type} (id: {args.id})"
        )
        await workflow.execute_activity(
            DispatchWithTemporalClient.run,
            args=(args,),
            start_to_close_timeout=timedelta(seconds=60),
        )
        log.info(
            f"ProducerActivityRepeated second dispatch for event: "
            f"{args.event_type} (id: {args.id})"
        )
        await workflow.execute_activity(
            DispatchWithTemporalClient.run,
            args=(args,),
            start_to_close_timeout=timedelta(seconds=60),
        )


@register_workflow
@workflow.defn
class ProducerSignal:
    @workflow.run
    async def run(self, args: EventDispatchInput) -> None:
        log.info(f"ProducerSignal dispatching event: {args.event_type} (id: {args.id})")
        await workflow.execute_activity(
            DispatchWithSignalAndStart.run,
            args=(args,),
            start_to_close_timeout=timedelta(seconds=60),
        )
