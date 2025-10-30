from __future__ import annotations

import logging
from datetime import timedelta

from temporalio import workflow

from pubsub.models.events import EventDispatchInput
from pubsub.temporal.registry import workflow as register_workflow
from pubsub.workflows.event_dispatcher import EventDispatcherWorkflow

log = logging.getLogger(__name__)


@register_workflow
@workflow.defn
class ProducerActivityWorkflow:
    @workflow.run
    async def run(self, input: EventDispatchInput) -> None:
        log.info(f"ProducerActivityWorkflow dispatching event: {input.event_type}")
        from pubsub.temporal.registry import get_activities

        activities = list(get_activities())
        spawn_activity = next(
            (a for a in activities if a.__name__ == "spawn_event_subscribers"), None
        )
        if spawn_activity is None:
            raise ValueError("spawn_event_subscribers activity not found")
        await workflow.execute_activity(
            spawn_activity,
            input,
            start_to_close_timeout=timedelta(seconds=60),
        )


@register_workflow
@workflow.defn
class ProducerWorkflowWorkflow:
    @workflow.run
    async def run(self, input: EventDispatchInput) -> None:
        log.info(f"ProducerWorkflowWorkflow dispatching event: {input.event_type}")
        handle = await workflow.start_child_workflow(
            EventDispatcherWorkflow.run,
            input,
            id=f"event-dispatcher-{input.event_type}-{workflow.info().workflow_id}",
        )
        await handle
