from pydio.injector import Injector
from pydio.provider import Provider

from pubsub.registry import SubscriberRegistry
from pubsub.temporal.utils import get_activities, get_workflows

provider = Provider()


@provider.provides("workflows")
def workflows(injector: Injector):
    return get_workflows(package_name="pubsub")


@provider.provides("activities")
def activities(injector: Injector):
    return get_activities(package_name="pubsub")


@provider.provides("subscribers")
def subscribers(injector: Injector) -> SubscriberRegistry:
    _workflows = injector.get("workflows")
    return SubscriberRegistry.create(_workflows)
