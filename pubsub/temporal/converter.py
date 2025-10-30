from __future__ import annotations

import inspect
from typing import Any, get_args, get_origin

from pydantic import BaseModel
from temporalio.api.common.v1 import Payload
from temporalio.converter import (
    CompositePayloadConverter,
    DataConverter,
    DefaultPayloadConverter,
    JSONPlainPayloadConverter,
)


class PydanticPayloadConverter(JSONPlainPayloadConverter):
    def to_payload(self, value: Any) -> Payload:
        if isinstance(value, BaseModel):
            payload = super().to_payload(value.model_dump())
            if payload is None:
                raise ValueError("Failed to convert Pydantic model to payload")
            return payload
        payload = super().to_payload(value)
        if payload is None:
            raise ValueError("Failed to convert value to payload")
        return payload

    def from_payload(self, payload: Payload, type_hint: type[Any] | None = None) -> Any:
        value = super().from_payload(payload, None)

        if type_hint is None:
            return value

        if _is_pydantic_model(type_hint):
            return type_hint.model_validate(value)

        origin = get_origin(type_hint)
        if origin is not None:
            args = get_args(type_hint)
            if args and _is_pydantic_model(args[0]):
                return args[0].model_validate(value)

        return value


def _is_pydantic_model(type_hint: type[Any]) -> bool:
    if not inspect.isclass(type_hint):
        return False
    try:
        return issubclass(type_hint, BaseModel)
    except TypeError:
        return False


def create_data_converter() -> DataConverter:
    default = DefaultPayloadConverter.default
    payload_converter = CompositePayloadConverter(
        PydanticPayloadConverter(),
        JSONPlainPayloadConverter(),
    )
    return DataConverter(  # type: ignore[call-arg]
        payload_converter=payload_converter,
        payload_codec=getattr(default, "payload_codec", None),
        failure_converter=getattr(default, "failure_converter", None),
    )
