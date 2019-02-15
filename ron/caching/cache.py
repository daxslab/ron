from beaker.cache import CacheManager

class CacheComponent(CacheManager):

    def __init__(self, *args, **kwargs):
        CacheManager.__init__(self, *args, **kwargs)