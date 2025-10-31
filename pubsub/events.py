from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class EventPayload(BaseModel):
    data: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)


class EventDispatchInput(BaseModel):
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for the event",
    )
    event_type: str = Field(description="Type of event to dispatch")
    payload: EventPayload | None = Field(default=None, description="Event payload")


class ConsumerWorkflowInput(BaseModel):
    payload: EventPayload | None = Field(default=None, description="Event payload")
