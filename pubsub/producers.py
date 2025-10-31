from __future__ import annotations

import logging
from datetime import timedelta
from typing import TypeAlias

from temporalio import activity, workflow

from pubsub.event_dispatchers import dispatch_event_with_signal, spawn_event_subscribers
from pubsub.events import ConsumerWorkflowInput, EventDispatchInput
from pubsub.temporal.utils import (
    get_all_workflows,
    get_subscribers,
    register_activity,
    register_workflow,
)

log = logging.getLogger(__name__)


@register_activity
@activity.defn
async def get_subscribers_activity(input: EventDispatchInput) -> None:
    log.error("all workflows ew", get_all_workflows())


@register_workflow
@workflow.defn
class EventDispatcherWorkflow:
    Args: TypeAlias = EventDispatchInput

    @workflow.run
    async def run(self, args: Args) -> None:
        log.info(f"Fetching subscribers for event type: {args.event_type}")
        await workflow.execute_activity(
            get_subscribers_activity,
            args=(args,),
            start_to_close_timeout=timedelta(seconds=60),
        )
        subscribers = get_subscribers(args.event_type)
        log.info(
            f"Found {len(subscribers)} subscribers for event type {args.event_type}"
        )
        for subscriber_workflow in subscribers:
            child_id = (
                f"{subscriber_workflow}-{args.event_type}-{workflow.info().workflow_id}"
            )
            consumer_input = ConsumerWorkflowInput(payload=args.payload)
            await workflow.start_child_workflow(
                subscriber_workflow,
                args=(consumer_input,),
                id=child_id,
            )


@register_workflow
@workflow.defn
class ProducerActivityWorkflow:
    Args: TypeAlias = EventDispatchInput

    @workflow.run
    async def run(self, args: Args) -> None:
        log.info(f"ProducerActivityWorkflow dispatching event: {args.event_type}")
        await workflow.execute_activity(
            spawn_event_subscribers,
            args=(args,),
            start_to_close_timeout=timedelta(seconds=60),
        )


@register_workflow
@workflow.defn
class ProducerWorkflowWorkflow:
    Args: TypeAlias = EventDispatchInput

    @workflow.run
    async def run(self, args: Args) -> None:
        log.info(f"ProducerWorkflowWorkflow dispatching event: {args.event_type}")
        handle = await workflow.start_child_workflow(
            EventDispatcherWorkflow.run,
            args,
            id=f"event-dispatcher-{args.event_type}-{workflow.info().workflow_id}",
        )
        await handle


@register_workflow
@workflow.defn
class ProducerSignalDispatcherWorkflow:
    Args: TypeAlias = EventDispatchInput

    @workflow.run
    async def run(self, args: Args) -> None:
        log.info(
            f"ProducerSignalDispatcherWorkflow dispatching event: {args.event_type}"
        )
        await workflow.execute_activity(
            dispatch_event_with_signal,
            args=(args,),
            start_to_close_timeout=timedelta(seconds=60),
        )
