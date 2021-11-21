import os

from exdir import base
from exdir import attribute


__all__ = ["DataSet"]


class DataSet(attribute.Attribute):
    """
    The DataSet uses a Attribute subclass to be able to serialize the data
    using a dictionary style interaction. The values are re-routed to be saved
    as their own individual files. This will ensure that the data will only be
    read from disk when required.
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
