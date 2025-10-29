from __future__ import annotations

from temporalio import workflow

from pubsub.temporal.registry import workflow as register_workflow


@register_workflow
@workflow.defn
class ProducerWorkflow:
    @workflow.run
    async def run(self, name: str | None = None) -> str:
        value = name or "world"
        return f"Hello, {value}!"


