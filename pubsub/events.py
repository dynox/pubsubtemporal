from __future__ import annotations

from pydantic import BaseModel, Field


class EventPayload(BaseModel):
    data: dict = Field(default_factory=dict)


class EventDispatchInput(BaseModel):
    id: str
    event_type: str = Field(description="Type of event to dispatch")
    payload: EventPayload | None = Field(default=None, description="Event payload")
