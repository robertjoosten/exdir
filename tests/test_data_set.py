import os
import shutil
import tempfile
import unittest
from exdir import data_set
from exdir import directory


class AttributeTestCase(unittest.TestCase):

    def setUp(self):
        self.path = os.path.join(tempfile.gettempdir(), "exdir")
        os.makedirs(self.path, mode=0o777)

        file_path = os.path.join(tempfile.gettempdir(), "exdir", "exdir.json")
        self.file = directory.File(self.path)
        self.data_set = data_set.DataSet(file_path, self.file)

    def tearDown(self):
        if os.path.isdir(self.path):
            shutil.rmtree(self.path, ignore_errors=False)

    # ------------------------------------------------------------------------

    def test_serializer(self):
        self.data_set["weights"] = [1] * 5
        self.data_set.commit()

        serializer = self.data_set.serializer("weights")
        self.assertTrue(serializer.exists())
