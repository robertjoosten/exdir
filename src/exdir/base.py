import os
import abc
import six
import sys
import shutil
import weakref
import collections

try:
    import ujson as json
except ImportError:
    import json


class WeakCache(abc.ABCMeta):
    """
    The weak meta class is a metaclass structure that will cache the created
    instances in a weak dictionary. This will ensure that the same class is
    returned returning the memory footprint.
    """
    def __init__(cls, *args, **kwargs):
        super(WeakCache, cls).__init__(*args, **kwargs)
        cls.cache = weakref.WeakValueDictionary()

    def __call__(cls, *args, **kwargs):
        key = str(args) + str(kwargs)
        try:
            instance = cls.cache[key]
        except KeyError:
            instance = super(WeakCache, cls).__call__(*args, **kwargs)
            cls.cache[key] = instance

        return instance


@six.add_metaclass(WeakCache)
class Object(object):
    """
    The base object contains a link to a path which at this stage can be a
    file or directory. A file object can be provided that will link back to
    the root of the exdir folder structure.
    """
    def __init__(self, path, f):
        self._path = os.path.normpath(path)
        self._file = f

    def __repr__(self):
        return "<{}.{} object to '{}'>".format(
            self.__class__.__module__,
            self.__class__.__name__,
            self.path
        )

    # ------------------------------------------------------------------------

    @property
    def path(self):
        """
        :return: Path
        :rtype: str
        """
        return self._path

    @property
    def file(self):
        """
        :return: File
        :rtype: File
        """
        return self._file

    # ------------------------------------------------------------------------

    def exists(self):
        """
        :return: Exist state
        :rtype: bool
        """
        return os.path.exists(self.path)

    def delete(self):
        """
        Remove the path from disk. If its a folder the entire directory
        including any content is removed.
        """
        if os.path.isdir(self.path):
            shutil.rmtree(self.path, ignore_errors=False)
        elif os.path.isfile(self.path):
            os.remove(self.path)


class Serializer(Object):
    """
    The serializer will allow for data to be read/written to/from disk using
    the json format. The data will only be retrieved from disk when requested.
    All changes are stored in memory first, these changes are marked as
    unsaved.
    """
    data_type = None

    def __init__(self, path, f):
        super(Serializer, self).__init__(path, f)
        self._data = self.data_type() if callable(self.data_type) else self.data_type
        self._initialized = False
        self._unsaved_changes = False

    # ------------------------------------------------------------------------

    def has_unsaved_changes(self):
        """
        :return: Unsaved changes state
        :rtype: bool
        """
        return self._unsaved_changes

    def set_unsaved_changes(self, state):
        """
        When unsaved changes are set the serializer object is attached or
        removed from the change log depending on the state.
        """
        if not state:
            self.file.unsaved_files.pop(self.path, None)
        else:
            self.file.unsaved_files[self.path] = self

        self._unsaved_changes = state

    # ------------------------------------------------------------------------

    @property
    def data(self):
        """
        If the data has not been initialized yet it will be read from disk
        using the json module.

        :return: Data
        """
        if not self._initialized and self.exists():
            try:
                with open(self.path, "r") as f:
                    self._data = json.load(f, object_pairs_hook=collections.OrderedDict)
                self._initialized = True
                self.set_unsaved_changes(False)
            except Exception as e:
                t, v, tb = sys.exc_info()
                message = "{} in '{}'.".format(e, self.path)
                try:
                    v = t(message)
                except TypeError:
                    v = RuntimeError(message)

                raise six.reraise(t, v, tb)

        return self._data

    @data.setter
    def data(self, data):
        """
        Set the internal data of the serializer to the provided data, please
        note that if the data is mutable it is up to the user to ensure that
        the data is not changed elsewhere. The data is validated against the
        data type, if they do not match a value error will be raised.

        :param data:
        """
        if self.data_type is not None and not isinstance(data, self.data_type):
            raise ValueError(
                "Unable to set data, expected type '{}' got '{}'.".format(
                    self.data_type.__name__,
                    data.__class__.__name__
                )
            )

        self._data = data
        self.set_unsaved_changes(True)

    # ------------------------------------------------------------------------

    def commit(self):
        """
        Write the current data to disk. If a file already exists it will
        simply be overwritten.
        """
        directory = os.path.split(self.path)[0]
        if not os.path.exists(directory):
            os.makedirs(directory, mode=0o777)

        with open(self.path, "w") as f:
            json.dump(self._data, f, indent=4)

        self._initialized = True
        self.set_unsaved_changes(False)

    def clear_cache(self, commit_changes=True):
        """
        Reset the internal data in the serializer. If there are unsaved
        changes they are committed first by default. After this the data
        variable is reset to 0 and the initialization state set to False.
        This will trigger the data to be read from disk again when requested.

        :param bool commit_changes:
        """
        if commit_changes and self.has_unsaved_changes():
            self.commit()
        else:
            self.set_unsaved_changes(False)

        self._data = self.data_type() if callable(self.data_type) else self.data_type
        self._initialized = False
