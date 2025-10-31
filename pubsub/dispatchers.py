from __future__ import annotations

import logging

from pydio.injector import Injector
from temporalio import activity
from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter

from pubsub.events import ConsumerWorkflowInput, EventDispatchInput
from pubsub.registry import SubscriberRegistry
from pubsub.temporal.settings import TemporalSettings
from pubsub.temporal.utils import register_activity

log = logging.getLogger(__name__)


@register_activity
class DispatchWithTemporalClient:
    def __init__(self, injector: Injector) -> None:
        self.injector = injector

    @activity.defn(name="DispatchWithTemporalClient")
    async def run(self, args: EventDispatchInput) -> None:
        registry: SubscriberRegistry = self.injector.inject("subscribers")
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
class DispatchWithSignalAndStart:
    def __init__(self, injector: Injector) -> None:
        self.injector = injector

    @activity.defn(name="DispatchWithSignalAndStart")
    async def run(self, args: EventDispatchInput) -> None:
        registry: SubscriberRegistry = self.injector.inject("subscribers")
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
