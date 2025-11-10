from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter

from pubsub.temporal.settings import TemporalSettings

if TYPE_CHECKING:
    from temporalio.client import WorkflowHandle

log = logging.getLogger(__name__)


class TemporalSearchRegistry:
    def __init__(self, client: Client | None = None) -> None:
        self._client = client
        self._settings = TemporalSettings()

    async def _get_client(self) -> Client:
        if self._client is None:
            self._client = await Client.connect(
                self._settings.address,
                namespace=self._settings.namespace,
                data_converter=pydantic_data_converter,
            )
        return self._client

    async def get_subscribers(self, event_type: str) -> list[WorkflowHandle]:
        client = await self._get_client()

        workflows: list[WorkflowHandle] = []
        query = f'subscribed_on = "{event_type}"'

        async for workflow_handle in client.list_workflows(query=query):
            workflows.append(workflow_handle)

        log.info(
            f"Found {len(workflows)} workflows subscribed to event type: {event_type}"
        )
        return workflows

    async def get_subscriber_workflow_types(self, event_type: str) -> list[str]:
        client = await self._get_client()

        workflow_types: set[str] = set()
        query = f'subscribed_on = "{event_type}"'

        async for workflow_handle in client.list_workflows(query=query):
            if workflow_handle.workflow_type:
                workflow_types.add(workflow_handle.workflow_type)

        result = list(workflow_types)
        log.info(
            f"Found {len(result)} unique workflow types "
            f"subscribed to event type: {event_type}"
        )
        return result
