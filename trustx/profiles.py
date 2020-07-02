import datetime
import json

from . import PublicKey, base58decode, base58encode


def _stringify(value):
    if isinstance(value, bytes):
        return base58encode(value)
    if isinstance(value, datetime.datetime):
        return value.isoformat()
    if isinstance(value, PublicKey):
        return value.encode()
    return value


class Block:
    @classmethod
    def serialize(self, data):
        text = json.dumps(data, default=_stringify, separators=(',', ':'),
                          sort_keys=True)
        return text.encode('utf-8')

    def verify(self):
        serialized = self.to.encode() + self.serialize(self.data)
        return self.by.verify(self.signature, data=serialized)


class Blocks:
    _BLOCK_DICT_REQUIRED_KEYS = set('by to data'.split())
    _BLOCK_DICT_OPTIONAL_KEYS = set()

    def __init__(self, values):
        self.__dict__ = values

    def __iter__(self):
        for sig, block_ in self.__dict__.items():
            block = Block()
            block.by = PublicKey(block_['by'])
            block.to = PublicKey(block_['to'])
            block.data = block_['data']
            block.signature = sig
            yield block

    def add(self, value, verify=True):
        if verify and not value.verify():
            raise ValueError('invalid block')
        self.__dict__[value.signature] = dict(by=value.by.encode(),
                                              to=value.to.encode(),
                                              data=value.data)

    def update(self, values):
        for value in values:
            self.add(value)

    def remove(self, signature):
        del self.__dict__[signature]

    @classmethod
    def parse(cls, block_dict, verify=True):
        r = cls({})
        required_keys = cls._BLOCK_DICT_REQUIRED_KEYS
        valid_keys = required_keys | cls._BLOCK_DICT_OPTIONAL_KEYS
        for signature, block_ in block_dict.items():
            included = block_.keys() & required_keys
            if included != required_keys:
                keys = ', '.join(required_keys - included)
                raise ValueError(f"missing required keys: {keys}")
            invalid_keys = block_.keys() - valid_keys
            if invalid_keys:
                keys = ', '.join(invalid_keys)
                raise ValueError(f"invalid keys: {keys}")
            block = Block()
            block.by = PublicKey(block_['by'])
            block.to = PublicKey(block_['to'])
            block.data = block_['data']
            if 'signed' in block.data:
                signed = block.data['signed']
                block.data['signed'] = datetime.datetime.fromisoformat(signed)
            block.signature = base58decode(signature)
            r.add(block, verify)
        return r


class Profile:
    def __init__(self, entity=None):
        self.__dict__ = entity
        self._changes = {}

    def __bool__(self):
        return bool(self.__dict__)

    def __getattr__(self, name):
        pass

    def __setattr__(self, name, value):
        if not name.startswith('_') and name not in self._changes:
                self._changes[name] = getattr(self, name)
        super().__setattr__(name, value)

    @property
    def key(self):
        if 'key' in self.__dict__:
            return PublicKey(self.__dict__['key'])

    @key.setter
    def key(self, value):
        self.__dict__['key'] = value.encode()

    @property
    def blocks(self):
        if 'blocks' not in self.__dict__:
            self.__dict__['blocks'] = {}
        return Blocks(self.__dict__['blocks'])


class Profiles:
    def __init__(self, storage):
        self.storage = storage

    def get(self, id=None, *, name=None, key=None, keyhash=None, hook=None):
        if name:
            idx = self.storage.profile_names.get(name)
        elif key:
            idx = self.storage.keys.get(key.hash)
        elif keyhash:
            idx = self.storage.keys.get(keyhash)
        elif hook:
            idx = self.storage.hooks.get(base58encode(hook.encode()))
        else:
            idx = None
        if idx:
            id = idx['profile_id']
        if id:
            entity = self.storage.profiles.get(id)
            return Profile(entity) if entity else None

    def put(self, profile):
        self.storage.profiles.put(vars(profile))

        if 'name' in profile._changes:
            old, new = profile._changes['name'], profile.name
            if old:
                self.storage.profile_names.delete(old)
            self.storage.profile_names.put(dict(id=new, profile_id=profile.id))

        if 'key' in profile._changes:
            old, new = profile._changes['key'], profile.key
            if old:
                self.storage.keys.delete(old.hash)
            self.storage.keys.put(dict(id=new.hash, profile_id=profile.id))

        if 'hook' in profile._changes:
            old, new = profile._changes['hook'], profile.hook
            if old:
                self.storage.hooks.delete(base58encode(old.encode()))
            new = base58encode(new.encode())
            self.storage.hooks.put(dict(id=new, profile_id=profile.id))


if __name__ == '__main__':
    import argparse
    import pathlib
    import sys
    import yaml
    from . import SecretKey

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command', required=True)

    subparser = subparsers.add_parser('sign')
    subparser.add_argument('--by', type=pathlib.Path, required=True)
    subparser.add_argument('--to', type=pathlib.Path, required=True)
    subparser.add_argument('data', type=pathlib.Path, nargs='?')

    subparser = subparsers.add_parser('verify')
    subparser.add_argument('data', type=pathlib.Path, nargs='?')

    args = parser.parse_args()

    if args.command == 'sign':
        by = SecretKey(args.by.read_bytes())
        to = PublicKey(args.to.read_bytes())
        data = args.data.read_bytes() if args.data else sys.stdin.buffer.read()
        data_dict = yaml.safe_load(data)
        sig = base58encode(by.sign(to.encode() + Block.serialize(data_dict)))
        blocks = {sig: dict(by=by.public_key, to=to, data=data_dict)}
        print(json.dumps(blocks, default=_stringify, indent=4))

    if args.command == 'verify':
        data = args.data.read_bytes() if args.data else sys.stdin.buffer.read()
        blocks = Blocks.parse(yaml.safe_load(data), verify=False)
        if not all(x.verify() for x in blocks):
            print('NG')
            exit(1)
        print('OK')
