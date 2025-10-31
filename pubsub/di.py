from pydio.injector import Injector
from pydio.provider import Provider

from pubsub.temporal.utils import get_activities, get_workflows

provider = Provider()


@provider.provides("workflows")
def workflows(injector: Injector):
    return get_workflows(package_name="pubsub")


@provider.provides("activities")
def activities(injector: Injector):
    return get_activities(package_name="pubsub")


@provider.provides("subscribers")
def subscribers(injector: Injector):
    _workflows = injector.get("workflows")


injector = Injector(provider)
