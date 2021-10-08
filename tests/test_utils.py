from unittest import TestCase

from pyevent import import_from_string, PyEvent


class TestImportFromString(TestCase):
    def test_ok(self):
        instance = import_from_string("pyevent:PyEvent")
        self.assertTrue(instance is PyEvent)

        instance = import_from_string("pyevent:PyEvent.run")
        self.assertTrue(instance is PyEvent.run)

    def test_bad_format(self):
        self.assertRaises(AssertionError, import_from_string, "")
        self.assertRaises(AssertionError, import_from_string, ":")
        self.assertRaises(AssertionError, import_from_string, "pyevent")
        self.assertRaises(AssertionError, import_from_string, "pyevent:")
        self.assertRaises(AssertionError, import_from_string, "PyEvent")
        self.assertRaises(AssertionError, import_from_string, ":PyEvent")

    def test_bad_module(self):
        self.assertRaises(ModuleNotFoundError, import_from_string, "bad_module:PyEvent")

    def test_bad_attr(self):
        self.assertRaises(AttributeError, import_from_string, "pyevent:bad_attr")
        self.assertRaises(AttributeError, import_from_string, "pyevent:PyEvent.bad_attr")
