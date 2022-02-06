import os
import shutil
import tempfile
import unittest
from exdir import attribute
from exdir import directory


class AttributeTestCase(unittest.TestCase):

    def setUp(self):
        self.path = os.path.join(tempfile.gettempdir(), "exdir")
        os.makedirs(self.path, mode=0o777)

        file_path = os.path.join(tempfile.gettempdir(), "exdir", "exdir.json")
        self.file = directory.File(self.path)
        self.attribute = attribute.Attribute(file_path, self.file)

    def tearDown(self):
        if os.path.isdir(self.path):
            shutil.rmtree(self.path, ignore_errors=False)

    # ------------------------------------------------------------------------

    def test_default(self):
        self.assertIsInstance(self.attribute.default, self.attribute.data_type)

    def test_unsaved_changes(self):
        self.attribute["key"] = "value"
        self.assertTrue(self.attribute.has_unsaved_changes())

    def test_magic_methods(self):
        self.attribute["key"] = "value"
        self.assertEqual(self.attribute["key"], "value")
        self.assertEqual(len(self.attribute), 1)
        self.assertIn("key", self.attribute)

        del self.attribute["key"]
        self.assertNotIn("key", self.attribute)
