from __future__ import annotations

import logging

from temporalio import activity
from temporalio.client import Client

from pubsub.models.events import ConsumerWorkflowInput, EventDispatchInput
from pubsub.temporal.converter import create_data_converter
from pubsub.temporal.registry import activity as register_activity, get_subscribers
from pubsub.temporal.settings import TemporalSettings

log = logging.getLogger(__name__)


@register_activity
@activity.defn
async def spawn_event_subscribers(input: EventDispatchInput) -> None:
    log.info(f"Fetching subscribers for event type: {input.event_type}")
    subscribers = get_subscribers(input.event_type)
    log.info(f"Found {len(subscribers)} subscribers for event type {input.event_type}")

    settings = TemporalSettings()
    data_converter = create_data_converter()
    client = await Client.connect(
        settings.address, namespace=settings.namespace, data_converter=data_converter
    )

    for subscriber_workflow in subscribers:
        workflow_name = subscriber_workflow.__name__
        workflow_id = (
            f"{workflow_name}-{input.event_type}-{activity.info().activity_id}"
        )
        log.info(f"Starting workflow {workflow_name} with id {workflow_id}")
        consumer_input = ConsumerWorkflowInput(payload=input.payload)
        await client.start_workflow(
            subscriber_workflow.run,
            args=(consumer_input,),
            id=workflow_id,
            task_queue=settings.task_queue,
        )
