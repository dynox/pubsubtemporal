from __future__ import annotations

import logging

from temporalio import workflow

from pubsub.events import ConsumerWorkflowInput
from pubsub.temporal.utils import subscribe

log = logging.getLogger(__name__)


@subscribe("event.a")
@workflow.defn
class ConsumerWorkflowA1:
    def __init__(self) -> None:
        self.event: ConsumerWorkflowInput | None = None

    @workflow.run
    async def run(self, input: ConsumerWorkflowInput | None = None) -> None:
        input_: ConsumerWorkflowInput = input or self.event
        log.info(f"ConsumerWorkflowA1 executed with input: {input_.model_dump()}")

    @workflow.signal
    async def process_event(self, input_: ConsumerWorkflowInput) -> None:
        log.info(f"Received signal A1: {input_.model_dump()}")
        self.event = input_


@subscribe("event.a")
@workflow.defn
class ConsumerWorkflowA2:
    def __init__(self) -> None:
        self.event: ConsumerWorkflowInput | None = None

    @workflow.run
    async def run(self, input: ConsumerWorkflowInput | None = None) -> None:
        input_: ConsumerWorkflowInput = input or self.event
        log.info(f"ConsumerWorkflowA2 executed with input: {input_.model_dump()}")

    @workflow.signal
    async def process_event(self, input_: ConsumerWorkflowInput) -> None:
        log.info(f"Received signal A2: {input_.model_dump()}")
        self.event = input_


@subscribe("event.b")
@workflow.defn
class ConsumerWorkflowB:
    def __init__(self) -> None:
        self.event: ConsumerWorkflowInput | None = None

    @workflow.run
    async def run(self, input: ConsumerWorkflowInput | None = None) -> None:
        input_: ConsumerWorkflowInput = input or self.event
        log.info(f"ConsumerWorkflowB executed with input: {input_.model_dump()}")

    @workflow.signal
    async def process_event(self, input_: ConsumerWorkflowInput) -> None:
        log.info(f"Received signal B: {input_.model_dump()}")
        self.event = input_
