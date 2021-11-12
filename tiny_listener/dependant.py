from typing import Callable, Any, Dict, Optional


class Depends:
    def __init__(
            self,
            dependency: Callable,  # TODO type _Callback
            use_cache: bool = True
    ):
        self.dependency = dependency  # TODO as_handler/callback
        self.use_cache = use_cache

    def __repr__(self) -> str:
        return "{}(dependency={}, use_cache={})".format(self.__class__.__name__,
                                                        self.dependency.__name__,
                                                        self.use_cache)


class Cache:
    def __init__(self):
        self.cache: Dict[Callable, Any] = {}  # todo type

    def get(self, depend: Depends) -> Optional[Any]:
        return self.cache.get(depend.dependency)

    def set(self, depend: Depends, val: Any):
        self.cache[depend.dependency] = val
