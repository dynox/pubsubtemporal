from __future__ import annotations

import inspect
import logging
from datetime import timedelta

from pydio.injector import Injector
from temporalio import activity, workflow

from pubsub.registry import SubscriberRegistry
from pubsub.temporal.utils import (
    register_activity,
    register_workflow,
)

log = logging.getLogger(__name__)


@register_activity
class LogRegistryActivity:
    def __init__(self, injector: Injector) -> None:
        self.injector = injector

    @activity.defn(name="LogRegistryActivity")
    async def run(self) -> None:
        registry: SubscriberRegistry = self.injector.inject("subscribers")

        workflows_list = self.injector.inject("workflows")
        workflows = {wf.__name__: wf for wf in workflows_list}
        activities = self.injector.inject("activities")

        log.info("=" * 80)
        log.info("REGISTRY REPORT")
        log.info("=" * 80)

        log.info("")
        log.info("REGISTERED WORKFLOWS")
        log.info("-" * 80)
        if workflows:
            for workflow_name, workflow_class in sorted(workflows.items()):
                module = inspect.getmodule(workflow_class)
                module_name = module.__name__ if module else "unknown"
                log.info(f"  • {workflow_name}")
                log.info(f"    Module: {module_name}")
                log.info(f"    Class: {workflow_class.__qualname__}")
        else:
            log.info("  (no workflows registered)")

        log.info("")
        log.info("REGISTERED ACTIVITIES")
        log.info("-" * 80)
        if activities:
            for activity_func in activities:
                activity_name = activity_func.__name__
                module = inspect.getmodule(activity_func)
                module_name = module.__name__ if module else "unknown"
                sig = inspect.signature(activity_func)
                log.info(f"  • {activity_name}")
                log.info(f"    Module: {module_name}")
                log.info(f"    Signature: {sig}")
        else:
            log.info("  (no activities registered)")

        log.info("")
        log.info("EVENT SUBSCRIPTIONS")
        log.info("-" * 80)
        if registry.subscribers:
            for event_type, subscriber_workflows in sorted(
                registry.subscribers.items()
            ):
                log.info(f"  Event Type: {event_type}")
                for subscriber in subscriber_workflows:
                    log.info(f"    → {subscriber.__name__}")
        else:
            log.info("  (no event subscriptions)")

        log.info("")
        log.info("SUMMARY")
        log.info("-" * 80)
        log.info(f"  Total Workflows: {len(workflows)}")
        log.info(f"  Total Activities: {len(activities)}")
        log.info(f"  Total Event Types: {len(registry.subscribers)}")
        total_subscribers = sum(len(subs) for subs in registry.subscribers.values())
        log.info(f"  Total Subscriptions: {total_subscribers}")
        log.info("=" * 80)


@register_workflow
@workflow.defn
class RegistryLoggerWorkflow:
    @workflow.run
    async def run(self) -> None:
        await workflow.execute_activity(
            LogRegistryActivity.run,
            start_to_close_timeout=timedelta(seconds=60),
        )
