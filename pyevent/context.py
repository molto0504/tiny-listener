from typing import Dict, Optional, Any, List, TYPE_CHECKING

from .job import Jobs

if TYPE_CHECKING:
    from .application import PyEvent


class __UniqueCTX(type):
    ctxs: Dict[str, 'Context'] = {}

    def __call__(cls, cid: Optional[str] = None, **scope) -> 'Context':
        if cid is None:
            return super().__call__(cid, **scope)
        if cid not in cls.ctxs:
            cls.ctxs[cid] = super().__call__(cid, **scope)
        ctx = cls.ctxs[cid]
        ctx.scope.update(scope)
        return ctx


class Context(metaclass=__UniqueCTX):
    def __init__(self, cid: Optional[str] = None, **scope) -> None:
        self.cid = cid
        self.scope: Dict[str, Any] = {"_app_": None, **scope}
        self.jobs = Jobs()
        self.errors: List[BaseException] = []

    @property
    def app(self) -> 'PyEvent':
        return self.scope["_app_"]

    @classmethod
    def exist(cls, cid: str) -> bool:
        return cid in cls.ctxs

    @classmethod
    def drop(cls, cid) -> 'Context':
        return cls.ctxs.pop(cid)

    def __call__(self, **scope) -> 'Context':
        return self.scope.update(scope) or self

    def __repr__(self) -> str:
        return "{}(cid={}, jobs_count={}, scope={}, errors={})".format(self.__class__.__name__,
                                                                       self.cid,
                                                                       len(self.jobs),
                                                                       self.scope,
                                                                       self.errors)


class Message(Dict):
    pass
