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


__all__ = [
    "Object",
    "Serializer"
]


class WeakCache(abc.ABCMeta):
    """
    The WeakCache is a metaclass that will cache the created instances in a
    weak dictionary. This will ensure that the same class is returned if the
    initialization arguments have already been used.
    """
    def __init__(cls, *args, **kwargs):
        super(WeakCache, cls).__init__(*args, **kwargs)
        cls.cache = weakref.WeakValueDictionary()

    def __call__(cls, *args, **kwargs):
        key = str(args) + str(kwargs)
        instance = cls.cache.get(key)
        if instance is None:
            instance = super(WeakCache, cls).__call__(*args, **kwargs)
            cls.cache[key] = instance

        return instance


@six.add_metaclass(WeakCache)
class Object(object):
    """
    The Object contains a link to the provided path, which can be a file or
    directory. It also contains a link to the File object. Any instance of
    the Object is weak cached which will make sure the same instance of the
    Object is returned to reduce the memory footprint.
    """
    def __init__(self, path, f):
        self._path = os.path.normpath(path)
        self._file = f

    def __eq__(self, other):
        if isinstance(other, Object):
            other = other.path

        return self.path == other

    def __ne__(self, other):
        if isinstance(other, Object):
            other = other.path

        return self.path != other

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


class Deferred(Object):
    """
    The Deferred objects will defer deletion until the commit method is
    called. The commit messaged are handled through the recording of
    unsaved changes.
    """
    def __init__(self, path, f):
        super(Deferred, self).__init__(path, f)
        self._unsaved_changes = False
        self._pending_deletion = False

    # ------------------------------------------------------------------------

    def pending_deletion(self):
        """
        :return: Pending deletion state
        :rtype: bool
        """
        return self._pending_deletion

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
        self.file.handle_unsaved_changes(self, state)
        self._unsaved_changes = state

    # ------------------------------------------------------------------------

    def commit(self):
        """
        Write the current data to disk. If the directory doesn't exist yet it
        will be created. If the file is set for deletion the Objects delete
        method is called.
        """
        if self._pending_deletion:
            if os.path.exists(self.path):
                super(Deferred, self).delete()

        self._pending_deletion = False
        self.set_unsaved_changes(False)

    def delete(self):
        """
        The deletion of the serializer is also deferred to the commit command.
        This will keep in line with the methodology where all changes are
        deferred.
        """
        self._pending_deletion = True
        self.set_unsaved_changes(True)


class Serializer(Deferred):
    """
    The Serializer can serialize the data to disk and read it back out. The
    data type can be provided as a class variable and this type is used as the
    default. Changes are stored in memory first but can be committed to disk,
    the File object keeps track of all these changes.
    """
    data_type = None

    def __init__(self, path, f):
        super(Serializer, self).__init__(path, f)
        self._data = self.default
        self._initialized = False

    # ------------------------------------------------------------------------

    @property
    def default(self):
        """
        :return: Default value
        """
        return self.data_type() if callable(self.data_type) else self.data_type

    # ------------------------------------------------------------------------

    @property
    def data(self):
        """
        Set the internal data by reading the file from disk if the path
        exists. This internal data is returned every time tis property is
        accessed.

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
        the data is not changed elsewhere to make sure the changes are
        recorded. The data is validated against the data type, if they do not
        match a value error will be raised.

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
        self._initialized = True
        self._pending_deletion = False
        self.set_unsaved_changes(True)

    # ------------------------------------------------------------------------

    def commit(self):
        """
        Write the current data to disk. If the directory doesn't exist yet it
        will be created. If the file is set for deletion the Objects delete
        method is called.
        """
        if self._pending_deletion:
            super(Serializer, self).commit()
        else:
            directory = os.path.split(self.path)[0]
            if not os.path.exists(directory):
                os.makedirs(directory, mode=0o777)

            with open(self.path, "w") as f:
                json.dump(self._data, f, indent=4)

        self._initialized = True
        self._pending_deletion = False
        self.set_unsaved_changes(False)

    def clear_cache(self, commit_changes=True):
        """
        Clear the internal data in the serializer. If there are unsaved
        changes it is possible to have them committed first. After this the
        data variable is reset to its default and the initialization state
        set to False. This will trigger the data to be read from disk again
        when requested.

        :param bool commit_changes:
        """
        if commit_changes and self.has_unsaved_changes():
            self.commit()
        else:
            self.set_unsaved_changes(False)

        self._data = self.default
        self._initialized = False
        self._pending_deletion = False

    def delete(self):
        """
        The deletion of the serializer is also deferred to the commit command.
        This will keep in line with the methodology where all changes are
        deferred.
        """
        super(Serializer, self).delete()
        self._data = self.default
        self._initialized = False
