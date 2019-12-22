"""Resources are the TaskActor's state which can be serialized, and
not necessary the Actor's output. This is specially useful to store
training models.
"""

import os
from pathlib import Path

try:
    import cPickle as pickle
except:
    import pickle
import shutil


class Resource(object):
    def __init__(self, rewritable=True):
        self.rewritable = rewritable

    def exists(self):
        raise NotImplementedError()

    def erase(self):
        raise NotImplementedError()

    def get_hash(self):
        raise NotImplementedError()


class FSResource(Resource):
    """
    Represent filesystem stored resources.

    Attributes:

        filepath (str): The file path.
    """

    def __init__(self, filepath, rewritable=True, make_dirs=False):
        super(FSResource, self).__init__(rewritable)
        self.filepath = os.path.abspath(str(filepath))
        self._str = str(filepath)
        self.make_dirs = make_dirs

    def exists(self):
        """
        Returns whatever the file exists.

        Returns:

            (bool): `True` if exists.
        """

        return os.path.exists(self.filepath)

    def erase(self):
        if os.path.exists(self.filepath):
            if os.path.isdir(self.filepath):
                shutil.rmtree(self.filepath)
            else:
                os.remove(self.filepath)

    def get_hash(self):
        if os.path.exists(self.filepath):
            return os.path.getmtime(self.filepath)
        return None

    def pickle_dump(self, obj):
        if self.make_dirs:
            Path(self.filepath).parent.mkdir(parents=True, exist_ok=True)

        with open(self.filepath, 'wb') as stream:
            pickle.dump(obj, stream, pickle.HIGHEST_PROTOCOL)
        return obj

    def pickle_load(self):
        with open(self.filepath, 'rb') as stream:
            return pickle.load(stream)

    def __str__(self):
        return self._str

    def __repr__(self):
        return "@FSResource: {}".format(self._str)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return (self.get_hash() == other.get_hash()
                and self.filepath == other.filepath)


class MultiResource(Resource):
    """Represent multiple resources

    Attributes:

        fsresource_list (:obj:`shaperetrieval.workflow.resource.FSResource):
         List of filesystem resource that composes this one.

    """

    def __init__(self, *fsresource_list, rewritable=True):
        super(MultiResource, self).__init__(rewritable)
        self.fsresource_list = fsresource_list

    def exists(self):
        """
        Returns whatever the file exists.

        Returns:

            (bool): `True` if exists.
        """

        return all((fsresource.exists() for fsresource in self.fsresource_list))

    def erase(self):
        for fsresource in self.fsresource_list:
            fsresource.erase()

    def get_hash(self):
        hash_list = [fsresource.get_hash()
                     for fsresource in self.fsresource_list]

        if any((hash_val is None for hash_val in hash_list)):
            return None

        return sum(hash_list)

    def __str__(self):
        return ('[' + ' '.join((str(fsresource)
                                for fsresource in self.fsresource_list)) + ']')

    def __repr__(self):
        return "@MultiFSResource: {}".format(str(self))

    def __getitem__(self, index):
        return self.fsresource_list[index]

    def __len__(self):
        return len(self.fsresource_list)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        other_set = set([res.get_hash() for res in other.fsresource_list])

        return all([res.get_hash() in other_set
                    for res in self.fsresource_list])


class NilResource(Resource):
    def __init__(self):
        super(NilResource, self).__init__()

    def exists(self):
        return False

    def get_hash(self):
        return None

    def __eq__(self, other):
        return isinstance(other, self.__class__)
