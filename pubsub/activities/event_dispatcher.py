from __future__ import annotations

import logging

from temporalio import activity
from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter

from pubsub.models.events import ConsumerWorkflowInput, EventDispatchInput
from pubsub.temporal.registry import get_subscribers, register_activity
from pubsub.temporal.settings import TemporalSettings

log = logging.getLogger(__name__)


@register_activity
@activity.defn
async def spawn_event_subscribers(input: EventDispatchInput) -> None:
    subscribers = get_subscribers(input.event_type)

    settings = TemporalSettings()
    client = await Client.connect(
        settings.address,
        namespace=settings.namespace,
        data_converter=pydantic_data_converter,
    )

    for subscriber_workflow in subscribers:
        workflow_name = subscriber_workflow.__name__
        workflow_id = (
            f"{workflow_name}-{input.event_type}-{activity.info().activity_id}"
        )
        consumer_input = ConsumerWorkflowInput(payload=input.payload)
        await client.start_workflow(
            subscriber_workflow.run,
            args=(consumer_input,),
            id=workflow_id,
            task_queue=settings.task_queue,
        )
