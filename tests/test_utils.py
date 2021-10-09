from unittest import TestCase

from listener import import_from_string, Listener


class TestImportFromString(TestCase):
    def test_ok(self):
        instance = import_from_string("listener:Listener")
        self.assertTrue(instance is Listener)

        instance = import_from_string("listener:Listener.run")
        self.assertTrue(instance is Listener.run)

    def test_bad_format(self):
        self.assertRaises(AssertionError, import_from_string, "")
        self.assertRaises(AssertionError, import_from_string, ":")
        self.assertRaises(AssertionError, import_from_string, "listener")
        self.assertRaises(AssertionError, import_from_string, "listener:")
        self.assertRaises(AssertionError, import_from_string, "Listener")
        self.assertRaises(AssertionError, import_from_string, ":Listener")

    def test_bad_module(self):
        self.assertRaises(ModuleNotFoundError, import_from_string, "bad_module:Listener")

    def test_bad_attr(self):
        self.assertRaises(AttributeError, import_from_string, "listener:bad_attr")
        self.assertRaises(AttributeError, import_from_string, "listener:Listener.bad_attr")
