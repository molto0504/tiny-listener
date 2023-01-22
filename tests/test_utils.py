from unittest import TestCase

from tiny_listener import Listener, import_from_string


class TestImportFromString(TestCase):
    def test_ok(self) -> None:
        instance = import_from_string("tiny_listener:Listener")
        self.assertTrue(instance is Listener)

        instance = import_from_string("tiny_listener:Listener.run")
        self.assertTrue(instance is Listener.run)

    def test_bad_format(self) -> None:
        self.assertRaises(AssertionError, import_from_string, "")
        self.assertRaises(AssertionError, import_from_string, ":")
        self.assertRaises(AssertionError, import_from_string, "tiny_listener")
        self.assertRaises(AssertionError, import_from_string, "tiny_listener:")
        self.assertRaises(AssertionError, import_from_string, "Listener")
        self.assertRaises(AssertionError, import_from_string, ":Listener")

    def test_bad_module(self) -> None:
        self.assertRaises(ModuleNotFoundError, import_from_string, "bad_module:Listener")

    def test_bad_attr(self) -> None:
        self.assertRaises(AttributeError, import_from_string, "tiny_listener:bad_attr")
        self.assertRaises(AttributeError, import_from_string, "tiny_listener:Listener.bad_attr")
