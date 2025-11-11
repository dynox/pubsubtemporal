from __future__ import annotations

import logging

from temporalio import workflow

from pubsub.events import EventPayload
from pubsub.temporal.utils import subscribe

log = logging.getLogger(__name__)


@subscribe("event.a", task_queue="pubsub-task-queue-secondary")
@workflow.defn
class ConsumerB:
    def __init__(self) -> None:
        self.event: EventPayload | None = None

    @workflow.run
    async def run(self, args: EventPayload | None = None) -> None:
        input_: EventPayload | None = args or self.event
        log.info(f"[ConsumerB] Executed with input: {input_}")

    @workflow.signal
    async def process_event(self, event: EventPayload) -> None:
        log.info(f"[ConsumerB] Received signal process_event: {event}")
        self.event = event
