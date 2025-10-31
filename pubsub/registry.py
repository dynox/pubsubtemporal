import logging
from typing import Type

log = logging.getLogger(__name__)


class SubscriberRegistry:
    def __init__(self) -> None:
        self.subscribers: dict[str, list[Type]] = {}

    def register(self, event_type: str, subscriber: Type) -> None:
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(subscriber)

    def get_subscribers(self, event_type: str) -> list[Type]:
        return self.subscribers.get(event_type, [])

    def pretty_print(self) -> None:
        for event_type, subscribers in self.subscribers.items():
            log.info(f"Event Type: {event_type}")
            for subscriber in subscribers:
                log.info(f"  Subscriber: {subscriber.__name__}")

    @classmethod
    def create(cls, workflows: list[Type]) -> "SubscriberRegistry":
        registry = cls()
        for workflow in workflows:
            if hasattr(workflow, "__subscribed_on__"):
                registry.register(workflow.__subscribed_on__, workflow)
        return registry
