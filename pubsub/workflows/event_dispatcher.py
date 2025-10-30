from __future__ import annotations

import logging

from temporalio import workflow

from pubsub.models.events import ConsumerWorkflowInput, EventDispatchInput
from pubsub.temporal.registry import get_subscribers
from pubsub.temporal.registry import workflow as register_workflow

log = logging.getLogger(__name__)


@register_workflow
@workflow.defn
class EventDispatcherWorkflow:
    @workflow.run
    async def run(self, input: EventDispatchInput) -> None:
        log.info(f"Fetching subscribers for event type: {input.event_type}")
        subscribers = get_subscribers(input.event_type)
        log.info(
            f"Found {len(subscribers)} subscribers for event type {input.event_type}"
        )

        for subscriber_workflow in subscribers:
            workflow_name = subscriber_workflow.__name__
            child_id = (
                f"{workflow_name}-{input.event_type}-{workflow.info().workflow_id}"
            )
            log.info(f"Starting child workflow {workflow_name} with id {child_id}")
            consumer_input = ConsumerWorkflowInput(payload=input.payload)
            await workflow.start_child_workflow(
                subscriber_workflow.run,
                args=(consumer_input,),
                id=child_id,
            )
