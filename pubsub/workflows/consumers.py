from __future__ import annotations

import logging

from temporalio import workflow

from pubsub.models.events import ConsumerWorkflowInput
from pubsub.temporal.registry import subscribe

log = logging.getLogger(__name__)


@subscribe("event.a")
@workflow.defn
class ConsumerWorkflowA1:
    @workflow.run
    async def run(self, input: ConsumerWorkflowInput) -> None:
        log.info(f"ConsumerWorkflowA1 executed with input: {input.model_dump()}")


@subscribe("event.a")
@workflow.defn
class ConsumerWorkflowA2:
    @workflow.run
    async def run(self, input: ConsumerWorkflowInput) -> None:
        log.info(f"ConsumerWorkflowA2 executed with input: {input.model_dump()}")


@subscribe("event.b")
@workflow.defn
class ConsumerWorkflowB:
    @workflow.run
    async def run(self, input: ConsumerWorkflowInput) -> None:
        log.info(f"ConsumerWorkflowB executed with input: {input.model_dump()}")
