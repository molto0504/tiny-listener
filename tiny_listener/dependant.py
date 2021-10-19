from typing import Callable, Any


class Depends:
    def __init__(
            self,
            dependency: Callable[..., Any],
            use_cache: bool = True
    ):
        self.dependency = dependency
        self.use_cache = use_cache

    def __repr__(self) -> str:
        return "{}(dependency={}, use_cache={})".format(self.__class__.__name__,
                                                        self.dependency.__name__,
                                                        self.use_cache)
