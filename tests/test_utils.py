from multiprocessing.pool import ThreadPool

import pytest

from tiny_listener import Listener, check_coro_func, import_from_string, is_main_thread


def test_import_from_string():
    assert import_from_string("tiny_listener:Listener") is Listener
    assert import_from_string("tiny_listener:Listener.run") is Listener.run


@pytest.mark.parametrize("path", ["", ":", "tiny_listener", "tiny_listener:", "Listener"])
def test_import_from_string_format_error(path: str):
    with pytest.raises(ImportError):
        import_from_string(path)


def test_import_from_string_module_not_found():
    with pytest.raises(ModuleNotFoundError):
        import_from_string("bad_module:Listener")


@pytest.mark.parametrize("path", ["tiny_listener:bad_attr", "tiny_listener:Listener.bad_attr"])
def test_import_from_string_attr_error(path: str):
    with pytest.raises(ImportError):
        import_from_string(path)


def test_is_main_thread():
    assert is_main_thread() is True

    with ThreadPool(1) as pool:
        result = pool.apply_async(lambda: is_main_thread())
        assert result.get(1) is False


def test_check_coro_func():
    def f():
        pass

    with pytest.raises(TypeError):
        check_coro_func(f)

    async def async_f():
        pass

    assert check_coro_func(async_f) is async_f
