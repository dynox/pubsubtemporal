from __future__ import annotations

import logging
from typing import Type

import temporalio.api.enums.v1 as enums
import temporalio.api.operatorservice.v1 as operatorservice
from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.service import RPCError, RPCStatusCode

from pubsub.temporal.settings import TemporalSettings

log = logging.getLogger(__name__)


def get_subscribed_event_types(workflows: list[Type]) -> set[str]:
    event_types: set[str] = set()
    for workflow in workflows:
        if hasattr(workflow, "__subscribed_on__"):
            event_type = getattr(workflow, "__subscribed_on__")
            if isinstance(event_type, str):
                event_types.add(event_type)
    return event_types


async def ensure_search_attribute_registered(
    client: Client, attribute_name: str, attribute_type: str = "Keyword"
) -> None:
    try:
        operator_svc = client.operator_service
        request = operatorservice.AddSearchAttributesRequest(
            search_attributes={
                attribute_name: enums.IndexedValueType.INDEXED_VALUE_TYPE_KEYWORD
            }
        )
        await operator_svc.add_search_attributes(request)
        log.info(f"Registered search attribute: {attribute_name} ({attribute_type})")
    except RPCError as e:
        if e.status == RPCStatusCode.ALREADY_EXISTS:
            log.debug(f"Search attribute {attribute_name} already exists")
        else:
            log.warning(
                f"Failed to register search attribute {attribute_name}: {e}. "
                "It may require admin privileges."
            )
    except Exception as e:
        log.warning(
            f"Failed to register search attribute {attribute_name}: {e}. "
            "It may already exist or require admin privileges."
        )


async def register_search_attributes_from_workflows(
    workflows: list[Type], client: Client | None = None
) -> None:
    event_types = get_subscribed_event_types(workflows)

    if not event_types:
        log.info(
            "No workflows with __subscribed_on__ found, "
            "skipping search attribute registration"
        )
        return

    if client is None:
        settings = TemporalSettings()
        client = await Client.connect(
            settings.address,
            namespace=settings.namespace,
            data_converter=pydantic_data_converter,
        )

    log.info(
        f"Registering search attribute 'subscribed_on' "
        f"for {len(event_types)} event types"
    )
    await ensure_search_attribute_registered(client, "subscribed_on", "Keyword")

    log.info(f"Found event types: {', '.join(sorted(event_types))}")
