class RouteError(Exception):
    pass


class EventAlreadyExists(Exception):
    pass


class EventNotFound(Exception):
    pass


class EventAlreadyDone(Exception):
    pass


class ContextNotFound(Exception):
    pass


class ContextAlreadyExists(Exception):
    pass


class DuplicateListener(Exception):
    pass


class ListenerNotFound(Exception):
    pass


class PathParamsError(Exception):
    pass
