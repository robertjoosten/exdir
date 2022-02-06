import os
import shutil
import tempfile
import unittest
from exdir import directory


class DirectoryTestCase(unittest.TestCase):

    def setUp(self):
        self.path = os.path.join(tempfile.gettempdir(), "exdir")
        os.makedirs(self.path, mode=0o777)

        self.file = directory.File(self.path)

    def tearDown(self):
        if os.path.isdir(self.path):
            shutil.rmtree(self.path, ignore_errors=False)

    # ------------------------------------------------------------------------

    def test_create_group(self):
        folder = os.path.join(self.path, "exdir")
        os.makedirs(folder, mode=0o777)

        with self.assertRaises(OSError):
            self.file.create_group("exdir")

    def test_require_group(self):
        child = self.file.require_group("exdir")
        self.assertFalse(child.exists())

    def test_parent(self):
        child = self.file.require_group("exdir")
        self.assertTrue(child.parent == self.file)

        with self.assertRaises(OSError):
            _ = self.file.parent

    def test_clear_cache(self):
        child = self.file.require_group("exdir")
        child.attr["key"] = "value"

        child.clear_cache(commit_changes=False)
        self.assertFalse("key" in child.attr)

    def test_magic_methods(self):
        self.file.require_group("exdir")  # not in memory
        self.assertEqual(len(self.file), 0)

        _ = self.file.require_group("exdir")
        self.assertEqual(len(self.file), 1)

        with self.assertRaises(KeyError):
            _ = self.file["exdir_not_existing"]

        del self.file["exdir"]
        self.assertTrue(len(self.file) == 0)


class FileTestCase(unittest.TestCase):

    def setUp(self):
        self.path = os.path.join(tempfile.gettempdir(), "exdir")
        os.makedirs(self.path, mode=0o777)

        self.file = directory.File(self.path)

    def tearDown(self):
        if os.path.isdir(self.path):
            shutil.rmtree(self.path, ignore_errors=False)

    # ------------------------------------------------------------------------

    def test_unsaved_changes(self):
        child = self.file.require_group("exdir")
        child.attr["key"] = "value"
        self.assertTrue(self.file.has_unsaved_changes())

        self.file.commit()
        self.assertFalse(self.file.has_unsaved_changes())