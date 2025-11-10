from __future__ import annotations

import logging

from temporalio import workflow

from pubsub.dispatchers import Dispatcher, SearchDispatcher
from pubsub.events import EventDispatchInput
from pubsub.temporal.utils import register_workflow

log = logging.getLogger(__name__)


@register_workflow
@workflow.defn
class Producer:
    @workflow.run
    async def run(self, args: EventDispatchInput) -> None:
        log.info(
            f"Producer starting dispatcher for event: {args.event_type} (id: {args.id})"
        )
        await workflow.execute_child_workflow(Dispatcher.run, args=(args,))


@register_workflow
@workflow.defn
class SearchProducer:
    @workflow.run
    async def run(self, args: EventDispatchInput) -> None:
        log.info(
            f"SearchProducer starting search dispatcher "
            f"for event: {args.event_type} (id: {args.id})"
        )
        await workflow.execute_child_workflow(SearchDispatcher.run, args=(args,))
