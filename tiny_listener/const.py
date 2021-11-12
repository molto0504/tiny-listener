from copy import copy
from typing import Dict, Type, DefaultDict, Any
from collections import defaultdict


class __Meta(type):
    cbs = {}

    def __new__(meta, cls, *args, **kwargs):
        if cls != "Base":
            meta.cbs[cls] = {
                "cb_do": [],
                "cb_pre_do": [],
                "cb_post_do": [],
                "cb_error_raise": [],
            }
        return super().__new__(meta, cls, *args, **kwargs)

    # def __call__(cls, *args, **kwargs):
    #     cls.do = cls.cbs[cls.__name__]
    #     return super().__call__(*args, **kwargs)


class Base(metaclass=__Meta):
    @classmethod
    def do(cls):
        def f(fn):
            cls.cbs[cls.__name__]["do"].append(fn)
        return f

    def foo(self):
        raise NotImplementedError()


class App1(Base):
    def foo(self):
        pass


class App2(Base):
    def foo(self):
        pass


def cb(): ...


@App1.do()
def foo():
    pass

# print(App1().do)

# print(App2().do)
# App1()
# App1.add(cb)
# App1()
# print(App1().default)
# print(App2().default)

