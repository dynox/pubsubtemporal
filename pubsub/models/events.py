from __future__ import annotations

from pydantic import BaseModel, Field


class EventPayload(BaseModel):
    data: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)


class ProducerWorkflowInput(BaseModel):
    name: str | None = Field(default=None, description="Optional name parameter")


class ProducerWorkflowOutput(BaseModel):
    message: str = Field(description="Greeting message")


class EventDispatchInput(BaseModel):
    event_type: str = Field(description="Type of event to dispatch")
    payload: EventPayload | None = Field(default=None, description="Event payload")


class ConsumerWorkflowInput(BaseModel):
    payload: EventPayload | None = Field(default=None, description="Event payload")

