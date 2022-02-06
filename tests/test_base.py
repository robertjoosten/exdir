import os
import shutil
import tempfile
import unittest
from exdir import base
from exdir import directory


class ObjectTestCase(unittest.TestCase):

    def setUp(self):
        self.path = os.path.join(tempfile.gettempdir(), "exdir.json")
        self.object = base.Object(self.path, None)
        f = open(self.path, "w")
        f.close()

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)

    # ------------------------------------------------------------------------

    def test_exists(self):
        self.assertTrue(self.object.exists())

    def test_delete(self):
        self.object.delete()
        self.assertFalse(self.object.exists())


class DeferredTestCase(unittest.TestCase):

    def setUp(self):
        self.path = os.path.join(tempfile.gettempdir(), "exdir")
        os.makedirs(self.path, mode=0o777, exist_ok=True)

        file_path = os.path.join(tempfile.gettempdir(), "exdir", "exdir.json")
        self.file = directory.File(self.path)
        self.deferred = base.Deferred(file_path, self.file)

    def tearDown(self):
        if os.path.isdir(self.path):
            shutil.rmtree(self.path, ignore_errors=False)

    # ------------------------------------------------------------------------

    def test_pending_deletion(self):
        f = open(self.deferred.path, "w")
        f.close()

        self.deferred.delete()
        self.assertTrue(self.deferred.pending_deletion())
        self.assertTrue(self.deferred.exists())

        self.deferred.commit()
        self.assertFalse(self.deferred.exists())

    def test_commit(self):
        f = open(self.deferred.path, "w")
        f.close()

        self.deferred.delete()
        self.deferred.commit()
        self.assertFalse(self.deferred.exists())


class SerializerTestCase(unittest.TestCase):

    def setUp(self):
        self.path = os.path.join(tempfile.gettempdir(), "exdir")
        os.makedirs(self.path, mode=0o777, exist_ok=True)

        file_path = os.path.join(tempfile.gettempdir(), "exdir", "exdir.json")
        f = directory.File(self.path)
        self.serializer = base.Serializer(file_path, f)

    def tearDown(self):
        if os.path.isdir(self.path):
            shutil.rmtree(self.path, ignore_errors=False)

    # ------------------------------------------------------------------------

    def test_default(self):
        self.assertIsNone(self.serializer.default)

    def test_commit(self):
        self.serializer.data = True
        self.serializer.commit()
        self.assertTrue(self.serializer.exists())
        self.assertFalse(self.serializer.has_unsaved_changes())
        self.assertFalse(self.serializer.pending_deletion())

    def test_unsaved_changes(self):
        self.serializer.data = True
        self.assertTrue(self.serializer.has_unsaved_changes())

        self.serializer.set_unsaved_changes(False)
        self.assertFalse(self.serializer.has_unsaved_changes())

    def test_clear_cache(self):
        self.serializer.data = False
        self.serializer.commit()
        self.serializer.data = True

        self.serializer.clear_cache(commit_changes=False)
        self.assertFalse(self.serializer.data)

        self.serializer.data = True
        self.serializer.clear_cache(commit_changes=True)
        self.assertTrue(self.serializer.data)