from __future__ import annotations

import logging
from typing import TypeAlias

from temporalio import workflow

from pubsub.events import ConsumerWorkflowInput
from pubsub.temporal.utils import register_workflow, subscribe

log = logging.getLogger(__name__)


@register_workflow
@subscribe("event.a")
@workflow.defn
class ConsumerA:
    Args: TypeAlias = ConsumerWorkflowInput | None

    def __init__(self) -> None:
        self.event: ConsumerWorkflowInput | None = None

    @workflow.run
    async def run(self, args: Args = None) -> None:
        input_: ConsumerWorkflowInput | None = args or self.event
        log.info(f"[ConsumerA] Executed with input: {input_}")

    @workflow.signal
    async def process_event(self, event: Args) -> None:
        log.info(f"[ConsumerA] Received signal process_event: {event}")
        self.event = event


@register_workflow
@subscribe("event.a")
@workflow.defn
class ConsumerB:
    Args: TypeAlias = ConsumerWorkflowInput | None

    def __init__(self) -> None:
        self.event: ConsumerWorkflowInput | None = None

    @workflow.run
    async def run(self, args: Args = None) -> None:
        input_: ConsumerWorkflowInput | None = args or self.event
        log.info(f"[ConsumerB] Executed with input: {input_}")

    @workflow.signal
    async def process_event(self, event: Args) -> None:
        log.info(f"[ConsumerB] Received signal process_event: {event}")
        self.event = event


@register_workflow
@subscribe("event.b")
@workflow.defn
class ConsumerC:
    Args: TypeAlias = ConsumerWorkflowInput | None

    def __init__(self) -> None:
        self.event: ConsumerWorkflowInput | None = None

    @workflow.run
    async def run(self, args: Args = None) -> None:
        input_: ConsumerWorkflowInput | None = args or self.event
        log.info(f"[ConsumerC] Executed with input: {input_}")

    @workflow.signal
    async def process_event(self, event: Args) -> None:
        log.info(f"[ConsumerC] Received signal process_event: {event}")
        self.event = event
