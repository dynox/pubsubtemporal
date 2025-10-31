from __future__ import annotations

import logging
from datetime import timedelta
from typing import Type

from pydio.injector import Injector
from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter

from pubsub.events import ConsumerWorkflowInput, EventDispatchInput
from pubsub.registry import SubscriberRegistry
from pubsub.temporal.settings import TemporalSettings
from pubsub.temporal.utils import register_activity, register_workflow

log = logging.getLogger(__name__)


@register_activity
class SpawnEventSubscribers:
    def __init__(self, injector: Injector) -> None:
        self.injector = injector

    @activity.defn(name="SpawnEventSubscribers")
    async def run(self, args: EventDispatchInput) -> None:
        registry: SubscriberRegistry = self.injector.get("subscribers")
        subscribers = registry.get_subscribers(args.event_type)

        if not subscribers:
            log.info(f"No subscribers found for event type: {args.event_type}")
            return

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
class DispatchEventWithSignal:
    def __init__(self, injector: Injector) -> None:
        self.injector = injector

    @activity.defn
    async def run(self, args: EventDispatchInput) -> None:
        registry: SubscriberRegistry = self.injector.get("subscribers")
        subscribers = registry.get_subscribers(args.event_type)

        if not subscribers:
            log.info(f"No subscribers found for event type: {args.event_type}")
            return

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
class GetSubscribersActivity:
    def __init__(self, injector: Injector) -> None:
        self.injector = injector

    @activity.defn(name="GetSubscribersActivity")
    async def run(self, args: EventDispatchInput) -> list[Type]:
        registry: SubscriberRegistry = self.injector.inject("subscribers")
        return registry.get_subscribers(args.event_type)


@register_workflow
@workflow.defn
class EventDispatcherWorkflow:
    @workflow.run
    async def run(self, args: EventDispatchInput) -> None:
        log.info(f"Fetching subscribers for event type: {args.event_type}")
        subscribers = await workflow.execute_activity(
            GetSubscribersActivity.run,
            args=(args,),
            start_to_close_timeout=timedelta(seconds=60),
        )
        for subscriber in subscribers:
            workflow_name = subscriber.__name__
            workflow_id = (
                f"{workflow_name}-{args.event_type}-{workflow.info().workflow_id}"
            )
            consumer_input = ConsumerWorkflowInput(payload=args.payload)
            await workflow.start_child_workflow(
                subscriber.run,
                args=(consumer_input,),
                id=workflow_id,
            )
