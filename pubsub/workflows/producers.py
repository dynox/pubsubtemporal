from __future__ import annotations

from datetime import timedelta
import logging

from temporalio import workflow

from pubsub.models.events import (
    EventDispatchInput,
    ProducerWorkflowInput,
    ProducerWorkflowOutput,
)
from pubsub.temporal.registry import workflow as register_workflow
from pubsub.workflows.event_dispatcher import EventDispatcherWorkflow

log = logging.getLogger(__name__)


@register_workflow
@workflow.defn
class ProducerWorkflow:
    @workflow.run
    async def run(self, input: ProducerWorkflowInput) -> ProducerWorkflowOutput:
        log.info("ProducerWorkflow run")
        value = input.name or "world"
        return ProducerWorkflowOutput(message=f"Hello, {value}!")


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
