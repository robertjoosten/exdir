import os

from exdir import base
from exdir import attribute


class DataSet(attribute.Attribute):
    """
    DataSet subclasses the attribute, but the data is rerouted to its own file
    which will ensure that the heavy data is only loaded when required. But a
    small header file is created to keep track of the data sets in the folder.
    """
    def __setitem__(self, key, value):
        """
        :param str key:
        :param value:
        """
        super(DataSet, self).__setitem__(key, None)
        self.serializer(key).data = value

    def __delitem__(self, item):
        """
        :param str item:
        """
        super(DataSet, self).__delitem__(item)
        self.serializer(item).delete()

    def __getitem__(self, item):
        """
        :param str item:
        """
        _ = self.data[item]  # validates data set
        return self.serializer(item).data

    # ------------------------------------------------------------------------

    def serializer(self, item):
        """
        :param str item:
        :return: Serializer
        :rtype: Serializer
        """
        directory = os.path.split(self.path)[0]
        return base.Serializer(os.path.join(directory, item), self.file)
