from typing import Any, Dict, Callable, Awaitable


Dependency = Callable[..., Awaitable[None]]


class Depends:
    def __init__(
            self,
            dependency: Dependency,
            use_cache: bool = True
    ) -> None:
        self.dependency = dependency
        self.use_cache = use_cache

    def __repr__(self) -> str:
        return "{}(dependency={}, use_cache={})".format(self.__class__.__name__,
                                                        self.dependency.__name__,
                                                        self.use_cache)


class Cache:
    def __init__(self) -> None:
        self._cache: Dict[Dependency, Any] = {}

    def get(self, depend: Depends) -> Any:
        return self._cache.get(depend.dependency)

    def set(self, depend: Depends, val: Any):
        self._cache[depend.dependency] = val

    def exist(self, depend: Depends) -> bool:
        return depend.dependency in self._cache

    def all(self) -> Dict[Dependency, Any]:
        return self._cache
