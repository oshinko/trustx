import pathlib
import pickle
import uuid


class Kind:
    def get(self, id):
        raise NotImplementedError

    def put(self, entity):
        raise NotImplementedError


class LocalStorageKind(Kind):
    def __init__(self, path):
        self.path = path

    def _get_entity_path(self, id):
        return (self.path / str(id)).with_suffix('.pickle')

    def get(self, id):
        path = self._get_entity_path(id)
        if path.is_file():
            return pickle.load(path.open('br'))

    def put(self, entity):
        if 'id' not in entity:
            entity['id'] = uuid.uuid4().hex
        path = self._get_entity_path(entity['id'])
        pickle.dump(entity, path.open('bw'))


class LocalStorage:
    kind_class = LocalStorageKind

    def __init__(self, path=pathlib.Path.cwd() / 'storage'):
        self.path = path
        self.path.mkdir(parents=True, exist_ok=True)

    def __getattr__(self, name):
        return self[name.replace('_', '-')]

    def __getitem__(self, key):
        for path in self.path.iterdir():
            if path.is_dir() and path.name == key:
                break
        else:
            path = self.path / key
            path.mkdir()
        return self.kind_class(path)
