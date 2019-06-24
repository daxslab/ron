import sys

try:
    from beaker.cache import CacheManager
except ModuleNotFoundError as e:
    print("Required beaker module, try to install it with 'pip install beaker'")
    sys.exit(1)

class CacheComponent(CacheManager):

    def __init__(self, *args, **kwargs):
        CacheManager.__init__(self, *args, **kwargs)
