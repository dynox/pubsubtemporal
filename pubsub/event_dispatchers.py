from __future__ import annotations

import logging
from datetime import timedelta
from typing import TypeAlias

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter

from pubsub.events import ConsumerWorkflowInput, EventDispatchInput
from pubsub.temporal.settings import TemporalSettings
from pubsub.temporal.utils import get_workflows, register_activity, register_workflow

log = logging.getLogger(__name__)


@register_activity
@activity.defn
class SpawnEventSubscribers:
    Args: TypeAlias = EventDispatchInput

    async def run(self, args: Args) -> None:
        workflows = get_workflows()
        subscribers = [
            wf
            for wf in workflows
            if getattr(wf, "__subscribed_on__", None) == args.event_type
        ]

        settings = TemporalSettings()
        client = await Client.connect(
            settings.address,
            namespace=settings.namespace,
            data_converter=pydantic_data_converter,
        )

        for subscriber_workflow in subscribers:
            workflow_name = subscriber_workflow.__name__
            workflow_id = (
                f"{workflow_name}-{args.event_type}-{activity.info().activity_id}"
            )
            consumer_input = ConsumerWorkflowInput(payload=args.payload)
            await client.start_workflow(
                subscriber_workflow.run,
                args=(consumer_input,),
                id=workflow_id,
                task_queue=settings.task_queue,
            )


@register_activity
@activity.defn
class DispatchEventWithSignal:
    Args: TypeAlias = EventDispatchInput

    async def run(self, args: Args) -> None:
        workflows = get_workflows()
        subscribers = [
            wf
            for wf in workflows
            if getattr(wf, "__subscribed_on__", None) == args.event_type
        ]

        settings = TemporalSettings()
        client = await Client.connect(
            settings.address,
            namespace=settings.namespace,
            data_converter=pydantic_data_converter,
        )

        consumer_input = ConsumerWorkflowInput(payload=args.payload)

        for subscriber_workflow in subscribers:
            workflow_name = subscriber_workflow.__name__
            workflow_id = f"{workflow_name}-{args.event_type}"

            try:
                await client.start_workflow(
                    subscriber_workflow.run,
                    id=workflow_id,
                    task_queue=settings.task_queue,
                    start_signal="process_event",
                    start_signal_args=[consumer_input],
                )
            except Exception:
                pass


@register_activity
@activity.defn
class GetSubscribersActivity:
    Args: TypeAlias = EventDispatchInput

    async def run(self, args: Args) -> None:
        pass


@register_workflow
@workflow.defn
class EventDispatcherWorkflow:
    Args: TypeAlias = EventDispatchInput

    @workflow.run
    async def run(self, args: Args) -> None:
        log.info(f"Fetching subscribers for event type: {args.event_type}")
        await workflow.execute_activity(
            GetSubscribersActivity,
            args=(args,),
            start_to_close_timeout=timedelta(seconds=60),
        )
        workflows = get_workflows()
        subscribers = [
            wf
            for wf in workflows
            if getattr(wf, "__subscribed_on__", None) == args.event_type
        ]
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
