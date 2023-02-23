class RouteError(Exception):
    pass


class EventAlreadyExists(Exception):
    pass


class EventNotFound(Exception):
    pass


class ContextNotFound(Exception):
    pass


class ContextAlreadyExists(Exception):
    pass


class DuplicateListener(Exception):
    pass
