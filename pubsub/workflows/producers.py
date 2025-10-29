from __future__ import annotations
import logging

from temporalio import workflow

from pubsub.temporal.registry import workflow as register_workflow


log = logging.getLogger(__name__)


@register_workflow
@workflow.defn
class ProducerWorkflow:
    @workflow.run
    async def run(self, name: str | None = None) -> str:
        log.info("ProducerWorkflow run")
        value = name or "world"
        return f"Hello, {value}!"
