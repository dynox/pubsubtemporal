from __future__ import annotations

import inspect
import logging
from typing import Dict, List, Type

from temporalio import workflow

from pubsub.temporal.utils import (
    get_activities,
    get_workflows,
    register_workflow,
)

log = logging.getLogger(__name__)


@register_workflow
@workflow.defn
class RegistryLoggerWorkflow:
    @workflow.run
    async def run(self) -> None:
        log.info("=" * 80)
        log.info("REGISTRY REPORT")
        log.info("=" * 80)

        workflows_list = list(get_workflows())
        workflows = {wf.__name__: wf for wf in workflows_list}
        activities = list(get_activities())

        subscriptions: Dict[str, List[Type]] = {}
        for wf in workflows_list:
            if hasattr(wf, "__subscribed_on__"):
                event_type = wf.__subscribed_on__
                if event_type not in subscriptions:
                    subscriptions[event_type] = []
                subscriptions[event_type].append(wf)

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
        if subscriptions:
            for event_type, subscriber_workflows in sorted(subscriptions.items()):
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
        log.info(f"  Total Event Types: {len(subscriptions)}")
        total_subscribers = sum(len(subs) for subs in subscriptions.values())
        log.info(f"  Total Subscriptions: {total_subscribers}")
        log.info("=" * 80)
