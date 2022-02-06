import os
import weakref
import collections

from exdir import base
from exdir import attribute
from exdir import data_set


__all__ = [
    "Directory",
    "File"
]


class Directory(base.Deferred, collections.Mapping):
    """
    The Directory represents a folder on disk. It can be assumed the
    directory is a relative path to the directory of the File object and
    allows for excess to child or parent directories and its file data,
    attributes and data sets. New directories can be required which means
    the Directory will be initialized if it exists or not. If a directory
    doesn't exist it will be stored in memory but still listed as one of
    the current Directories children.
    """
    def __init__(self, path, f):
        super(Directory, self).__init__(path, f)
        self._memory = weakref.WeakValueDictionary()
        self._meta = attribute.Attribute(os.path.join(self.path, ".meta"), self.file)
        self._attr = attribute.Attribute(os.path.join(self.path, ".attributes"), self.file)
        self._data_set = data_set.DataSet(os.path.join(self.path, ".data_sets"), self.file)

    def __getitem__(self, item):
        """
        :param str item:
        :return: Directory
        :rtype: Directory
        :raise KeyError: When the constructed path doesn't exist.
        :raise KeyError: When the constructed path isn't a directory.
        :raise KeyError: When the constructed path exists, but is pending deletion.
        """
        if item in self._memory:
            return self._memory[item]

        path = os.path.join(self.path, item)
        path = os.path.normpath(path)
        if not os.path.exists(path):
            raise KeyError("Path '{}' doesn't exist.".format(self.path))
        elif not os.path.isdir(path):
            raise KeyError("Path '{}' is not a directory.".format(self.path))

        obj = Directory(path, self.file)
        if obj.pending_deletion():
            raise KeyError("Path '{}' exists, but is pending deletion.".format(self.path))

        return obj

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
        directories = set(directories + list(self._memory.keys()))
        for name in sorted(directories):
            obj = Directory(os.path.join(self.path, name), self.file)
            if not obj.pending_deletion():
                yield obj

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

        directory_object = Directory(directory, self.file)
        self._memory[name] = directory_object
        return directory_object

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
        for cls in [base.Serializer, attribute.Attribute, data_set.DataSet]:
            for instance in cls.cache.values():
                if instance.path.startswith(self.path):
                    instance.clear_cache(commit_changes=commit_changes)


class File(Directory):
    def __init__(self, directory):
        super(File, self).__init__(directory, self)
        self.unsaved_changes = {}

        if not os.path.exists(self.path):
            raise OSError("File '{}' doesn't exist.".format(self.path))

    # ------------------------------------------------------------------------

    def has_unsaved_changes(self):
        """
        :return: Unsaved files state
        :rtype: bool
        """
        return bool(self.unsaved_changes)

    def handle_unsaved_changes(self, serializer, add=True):
        """
        :param Serializer serializer:
        :param bool add:
        """
        if add:
            self.unsaved_changes[serializer.path] = serializer
        else:
            self.unsaved_changes.pop(self.path, None)

    # ------------------------------------------------------------------------

    def commit(self):
        """
        Loop over all unsaved changes and commit them individually. This will
        force any changes within the file to be written to disk.
        """
        for serializer in self.unsaved_changes.values():
            serializer.commit()

        self.unsaved_changes.clear()
