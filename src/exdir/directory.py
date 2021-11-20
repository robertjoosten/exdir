import os
import collections

from exdir import base
from exdir import attribute
from exdir import data_set


class Directory(base.Object, collections.Mapping):
    """
    The directory class is representation of a folder on disk. It can be
    assumed the directory is a relative path to the 'file' directory and
    allows for excess to child or parent directories and its meta data,
    attributes and data sets. New directories can be required which means
    they will be created if they do not exist yet.
    """
    def __init__(self, path, f):
        super(Directory, self).__init__(path, f)

        self._meta = attribute.Attribute(os.path.join(self.path, ".meta"), self.file)
        self._attr = attribute.Attribute(os.path.join(self.path, ".attributes"), self.file)
        self._data_set = data_set.DataSet(os.path.join(self.path, ".data_set"), self.file)

    def __getitem__(self, item):
        """
        :param str item:
        :return: Directory
        :rtype: Directory
        :raise KeyError: When the constructed path doesn't exist.
        :raise KeyError: When the constructed path isn't a storage.
        """
        path = os.path.join(self.path, item)
        path = os.path.normpath(path)
        if not os.path.exists(path):
            raise KeyError("Path '{}' doesn't exist.")

        if not os.path.isdir(path):
            raise KeyError("Path '{}' is not a storage.")

        return Directory(path, self.file)

    def __delitem__(self, item):
        """
        :param str item:
        """
        self[item].delete()

    def __iter__(self):
        """
        :return: Directories
        :rtype: generator[Directory]
        """
        directories = next(os.walk(str(self.path)))[1]
        for name in sorted(directories):
            yield Directory(os.path.join(self.path, name), self.file)

    def __len__(self):
        """
        :return: Length
        :rtype: int
        """
        return len([a for a in self])

    # ------------------------------------------------------------------------

    @property
    def parent(self):
        """
        :return: Parent
        :rtype: Directory/File
        :raise RuntimeError: When the hierarchy is already at root.
        """
        parent_directory = os.path.split(self.path)[0]
        if self.file.path == self.path:
            raise OSError("Unable to retrieve parent from File.")
        elif parent_directory == self.file.path:
            return self.file
        else:
            return Directory(parent_directory, self.file)

    # ------------------------------------------------------------------------

    @property
    def meta(self):
        """
        :return: Meta
        :rtype: Attribute
        """
        return self._meta

    @property
    def attr(self):
        """
        :return: Attribute
        :rtype: Attribute
        """
        return self._attr

    @property
    def data_set(self):
        """
        :return: Data set
        :rtype: DataSet
        """
        return self._data_set

    # ------------------------------------------------------------------------

    def create_group(self, name):
        """
        :param str name:
        :return: Directory
        :rtype: Directory
        :raise OSError: When the storage already exists.
        """
        directory = os.path.join(self.path, name)
        if os.path.exists(directory):
            raise OSError("Unable to create folder from path '{}', "
                          "it already exists.".format(directory))

        return Directory(directory, self.file)

    def require_group(self, name):
        """
        :param str name:
        :return: Directory
        :rtype: Directory
        """
        try:
            return self[name]
        except KeyError:
            return self.create_group(name)

    # ------------------------------------------------------------------------

    def clear_cache(self, commit_changes=True):
        """
        Loop all cached attributes and data sets and if the are a child of the
        current directory they will have their cache cleared. Meaning that if
        the data is requested again it will be retrieved from disk.

        :param bool commit_changes:
        """
        for attr in attribute.Attribute.cache.values():
            if attr.path.startswith(self.path):
                attr.clear_cache(commit_changes=commit_changes)

        for data in data_set.DataSet.cache.values():
            if data.path.startswith(self.path):
                data.clear_cache(commit_changes=commit_changes)


class File(Directory):
    def __init__(self, directory):
        super(File, self).__init__(directory, self)
        self.unsaved_files = {}

        if not os.path.exists(self.path):
            raise OSError("File '{}' doesn't exist.".format(self.path))

    # ------------------------------------------------------------------------

    def has_unsaved_files(self):
        """
        :return: Unsaved files state
        :rtype: bool
        """
        return bool(self.unsaved_files)

    def commit(self):
        """
        Loop over all unsaved changes and commit them individually. This will
        force any changes within the file to be written to disk.
        """
        for serializer in self.unsaved_files.values():
            serializer.commit()
