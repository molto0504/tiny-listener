from unittest import TestCase

from tiny_listener import import_from_string, Listener


class TestImportFromString(TestCase):
    def test_ok(self):
        instance = import_from_string("tiny_listener:Listener")
        self.assertTrue(instance is Listener)

        instance = import_from_string("tiny_listener:Listener.run")
        self.assertTrue(instance is Listener.run)

    def test_bad_format(self):
        self.assertRaises(AssertionError, import_from_string, "")
        self.assertRaises(AssertionError, import_from_string, ":")
        self.assertRaises(AssertionError, import_from_string, "tiny_listener")
        self.assertRaises(AssertionError, import_from_string, "tiny_listener:")
        self.assertRaises(AssertionError, import_from_string, "Listener")
        self.assertRaises(AssertionError, import_from_string, ":Listener")

    def test_bad_module(self):
        self.assertRaises(ModuleNotFoundError, import_from_string, "bad_module:Listener")

    def test_bad_attr(self):
        self.assertRaises(AttributeError, import_from_string, "tiny_listener:bad_attr")
        self.assertRaises(AttributeError, import_from_string, "tiny_listener:Listener.bad_attr")
