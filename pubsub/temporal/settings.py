from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TemporalSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TEMPORAL_", env_file=".env", env_file_encoding="utf-8"
    )

    address: str = Field(default="localhost:7233")
    namespace: str = Field(default="default")
    task_queue: str = Field(default="pubsub-task-queue")
    task_queue_secondary: str = Field(default="pubsub-task-queue-secondary")
