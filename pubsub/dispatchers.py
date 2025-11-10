from __future__ import annotations

import logging
from datetime import timedelta

from pydio.injector import Injector
from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.common import WorkflowIDReusePolicy
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.exceptions import WorkflowAlreadyStartedError

from pubsub.events import EventDispatchInput, EventPayload
from pubsub.registry import SubscriberRegistry
from pubsub.search_registry import TemporalSearchRegistry
from pubsub.temporal.settings import TemporalSettings
from pubsub.temporal.utils import register_activity, register_workflow

log = logging.getLogger(__name__)


@register_workflow
@workflow.defn
class Dispatcher:
    @workflow.run
    async def run(self, args: EventDispatchInput) -> None:
        await workflow.execute_activity(
            DispatcherActivity.run,
            args=(args,),
            start_to_close_timeout=timedelta(seconds=30),
        )


@register_activity
class DispatcherActivity:
    def __init__(self, injector: Injector) -> None:
        self.injector = injector

    @activity.defn(name="DispatcherActivity")
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
            workflow_id = f"{workflow_name}-{args.event_type}-{args.id}"
            consumer_input = args.payload or EventPayload()
            try:
                await client.start_workflow(
                    subscriber_workflow.run,
                    args=(consumer_input,),
                    id=workflow_id,
                    task_queue=settings.task_queue,
                    id_reuse_policy=WorkflowIDReusePolicy.REJECT_DUPLICATE,
                )
            except WorkflowAlreadyStartedError:
                log.info(f"Workflow {workflow_id} already started")


@register_workflow
@workflow.defn
class SearchDispatcher:
    @workflow.run
    async def run(self, args: EventDispatchInput) -> None:
        await workflow.execute_activity(
            SearchDispatcherActivity.run,
            args=(args,),
            start_to_close_timeout=timedelta(seconds=30),
        )


@register_activity
class SearchDispatcherActivity:
    def __init__(self, injector: Injector) -> None:
        self.injector = injector

    @activity.defn(name="SearchDispatcherActivity")
    async def run(self, args: EventDispatchInput) -> None:
        settings = TemporalSettings()
        client = await Client.connect(
            settings.address,
            namespace=settings.namespace,
            data_converter=pydantic_data_converter,
        )

        registry = TemporalSearchRegistry(client=client)
        workflow_type_names = await registry.get_subscriber_workflow_types(
            args.event_type
        )

        if not workflow_type_names:
            log.info(
                f"No workflow types found subscribed to event type: {args.event_type}"
            )
            return

        all_workflows = list(self.injector.inject("workflows"))
        workflow_type_map = {wf.__name__: wf for wf in all_workflows}

        subscriber_workflows = [
            workflow_type_map[type_name]
            for type_name in workflow_type_names
            if type_name in workflow_type_map
        ]

        if not subscriber_workflows:
            log.info(
                f"No matching workflow classes found for event type: {args.event_type}"
            )
            return

        for subscriber_workflow in subscriber_workflows:
            workflow_name = subscriber_workflow.__name__
            workflow_id = f"{workflow_name}-{args.event_type}-{args.id}"
            consumer_input = args.payload or EventPayload()
            try:
                await client.start_workflow(
                    subscriber_workflow.run,
                    args=(consumer_input,),
                    id=workflow_id,
                    task_queue=settings.task_queue,
                    id_reuse_policy=WorkflowIDReusePolicy.REJECT_DUPLICATE,
                )
            except WorkflowAlreadyStartedError:
                log.info(f"Workflow {workflow_id} already started")
