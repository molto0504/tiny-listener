class ListenerError(Exception):
    pass


class RouteError(ListenerError):
    pass


class EventAlreadyExists(ListenerError):
    pass


class EventNotFound(ListenerError):
    pass


class EventAlreadyDone(ListenerError):
    pass


class ContextNotFound(ListenerError):
    pass


class ContextAlreadyExists(ListenerError):
    pass


class DuplicateListener(ListenerError):
    pass


class ListenerNotFound(ListenerError):
    pass


class PathParamsError(ListenerError):
    pass


class EventDataError(ListenerError):
    pass
