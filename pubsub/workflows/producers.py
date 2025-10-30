from __future__ import annotations

import logging
from datetime import timedelta

from temporalio import workflow

from pubsub.activities.event_dispatcher import spawn_event_subscribers
from pubsub.activities.signal_dispatcher import dispatch_event_with_signal
from pubsub.models.events import EventDispatchInput
from pubsub.temporal.registry import register_workflow
from pubsub.workflows.event_dispatcher import EventDispatcherWorkflow

log = logging.getLogger(__name__)


@register_workflow
@workflow.defn
class ProducerActivityWorkflow:
    @workflow.run
    async def run(self, input: EventDispatchInput) -> None:
        log.info(f"ProducerActivityWorkflow dispatching event: {input.event_type}")
        await workflow.execute_activity(
            spawn_event_subscribers,
            args=(input,),
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


@register_workflow
@workflow.defn
class ProducerSignalDispatcherWorkflow:
    @workflow.run
    async def run(self, input: EventDispatchInput) -> None:
        log.info(
            f"ProducerSignalDispatcherWorkflow dispatching event: {input.event_type}"
        )
        await workflow.execute_activity(
            dispatch_event_with_signal,
            args=(input,),
            start_to_close_timeout=timedelta(seconds=60),
        )
