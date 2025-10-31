from __future__ import annotations

import logging

from temporalio import workflow

from pubsub.events import ConsumerWorkflowInput
from pubsub.temporal.utils import register_workflow, subscribe

log = logging.getLogger(__name__)


@register_workflow
@subscribe("event.a")
@workflow.defn
class ConsumerA:
    def __init__(self) -> None:
        self.event: ConsumerWorkflowInput | None = None

    @workflow.run
    async def run(self, args: ConsumerWorkflowInput | None = None) -> None:
        input_: ConsumerWorkflowInput | None = args or self.event
        log.info(f"[ConsumerA] Executed with input: {input_}")

    @workflow.signal
    async def process_event(self, event: ConsumerWorkflowInput) -> None:
        log.info(f"[ConsumerA] Received signal process_event: {event}")
        self.event = event


@register_workflow
@subscribe("event.a")
@workflow.defn
class ConsumerB:
    def __init__(self) -> None:
        self.event: ConsumerWorkflowInput | None = None

    @workflow.run
    async def run(self, args: ConsumerWorkflowInput | None = None) -> None:
        input_: ConsumerWorkflowInput | None = args or self.event
        log.info(f"[ConsumerB] Executed with input: {input_}")

    @workflow.signal
    async def process_event(self, event: ConsumerWorkflowInput) -> None:
        log.info(f"[ConsumerB] Received signal process_event: {event}")
        self.event = event


@register_workflow
@subscribe("event.b")
@workflow.defn
class ConsumerC:
    def __init__(self) -> None:
        self.event: ConsumerWorkflowInput | None = None

    @workflow.run
    async def run(self, args: ConsumerWorkflowInput | None = None) -> None:
        input_: ConsumerWorkflowInput | None = args or self.event
        log.info(f"[ConsumerC] Executed with input: {input_}")

    @workflow.signal
    async def process_event(self, event: ConsumerWorkflowInput) -> None:
        log.info(f"[ConsumerC] Received signal process_event: {event}")
        self.event = event
