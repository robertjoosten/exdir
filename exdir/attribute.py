import collections

from exdir import base


__all__ = ["Attribute"]


class Attribute(base.Serializer, collections.MutableMapping):
    """
    The Attribute uses a MutableMapping subclass to be able to serialize the
    data using a dictionary style interaction.
    """
    data_type = collections.OrderedDict

    def __setitem__(self, key, value):
        """
        :param str key:
        :param value:
        """
        self.data[key] = value
        self.set_unsaved_changes(True)

    def __delitem__(self, item):
        """
        :param str item:
        """
        del self.data[item]
        self.set_unsaved_changes(True)

    def __getitem__(self, item):
        """
        :param str item:
        """
        return self.data[item]

    def __len__(self):
        """
        :return: Length
        :rtype: int
        """
        return len(self.data)

    def __iter__(self):
        """
        :return: Keys
        :rtype: generator[str]
        """
        for key in self.data.keys():
            yield key
