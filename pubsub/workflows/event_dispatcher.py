from __future__ import annotations

from datetime import timedelta
import logging

from temporalio import activity, workflow

from pubsub.models.events import ConsumerWorkflowInput, EventDispatchInput
from pubsub.temporal.registry import (
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
    @workflow.run
    async def run(self, input: EventDispatchInput) -> None:
        log.info(f"Fetching subscribers for event type: {input.event_type}")
        await workflow.execute_activity(
            get_subscribers_activity,
            args=(input,),
            start_to_close_timeout=timedelta(seconds=60),
        )
        subscribers = get_subscribers(input.event_type)
        log.info(
            f"Found {len(subscribers)} subscribers for event type {input.event_type}"
        )
        for subscriber_workflow in subscribers:
            child_id = f"{subscriber_workflow}-{input.event_type}-{workflow.info().workflow_id}"
            consumer_input = ConsumerWorkflowInput(payload=input.payload)
            await workflow.start_child_workflow(
                subscriber_workflow,
                args=(consumer_input,),
                id=child_id,
            )
