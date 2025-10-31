from pydio.injector import Injector
from pydio.provider import Provider

provider = Provider()


@provider.provides
def registry(injector: Injector):
    pass
