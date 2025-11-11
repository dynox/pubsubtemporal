from __future__ import annotations  # noqa: I001

import asyncio

from pubsub.temporal.settings import TemporalSettings
from pubsub.worker import run_worker_with_packages


async def run_worker() -> None:
    """Secondary worker - loads domain_b packages only."""
    settings = TemporalSettings()
    await run_worker_with_packages(
        workflow_packages=["pubsub.domain_b"],
        activity_packages=["pubsub.domain_b"],
        task_queue=settings.task_queue_secondary,
    )


if __name__ == "__main__":
    asyncio.run(run_worker())
