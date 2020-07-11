import datetime
import hashlib
import json

import yaml

from . import PublicKey, base58decode, base58encode


def _stringify(value, target=json):
    if isinstance(value, bytes):
        return base58encode(value)
    if isinstance(value, PublicKey):
        return value.hash
    if target == json and isinstance(value, datetime.datetime):
        return value.isoformat()
    return value


def _stringify_yaml_walk(data, result=None):
    r = result or {}
    for k, v in data:
        if isinstance(v, dict):
            r[k] = _stringify_yaml_walk(v.items())
        elif isinstance(v, (list, set, tuple)):
            r[k] = _stringify_yaml_walk(enumerate(v), [])
        else:
            r[k] = _stringify(v, yaml)
    return r


def _stringify_yaml(data, target=yaml):
    if isinstance(data, dict):
        return _stringify_yaml_walk(data.items())
    elif isinstance(data, (list, set, tuple)):
        return _stringify_yaml_walk(enumerate(data), [])
    return _stringify(data, yaml)


class Block:
    @classmethod
    def serialize(self, data):
        return json.dumps(data, default=_stringify, separators=(',', ':'),
                          sort_keys=True).encode('utf-8')

    def verify(self):
        data = dict(by=self.by, to=self.to, data=self.data)
        return self.by.verify(self.signature, data=self.serialize(data))


class Blocks:
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


class Profile:
    def __init__(self, entity=None, key=None):
        if entity:
            self.__dict__ = entity
        if key:
            self._key = key
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
        return self._key

    @key.setter
    def key(self, value):
        self.__dict__['key'] = value.hash
        self._key = value

    @property
    def blocks(self):
        if 'blocks' not in self.__dict__:
            self.__dict__['blocks'] = {}
        return Blocks(self.__dict__['blocks'])


class Profiles:
    _BLOCK_REQUIRED_KEYS = set('by to data'.split())
    _BLOCK_OPTIONAL_KEYS = set()

    def __init__(self, storage):
        self.storage = storage

    def __len__(self):
        return len(self.storage.profiles)

    def get(self, id=None, *, name=None, key=None, keyhash=None, hook=None):
        idx = None
        idx_key = None
        if name:
            idx = self.storage.profile_names.get(name)
        elif key:
            idx = self.storage.keys.get(key.hash)
            idx_key = idx
        elif keyhash:
            idx = self.storage.keys.get(keyhash)
            idx_key = idx
        elif hook:
            hook_id = hashlib.sha1(hook.encode()).hexdigest()
            idx = self.storage.hooks.get(hook_id)
        if idx:
            id = idx['profile_id']
        if id:
            entity = self.storage.profiles.get(id)
            if entity:
                if 'key' in entity:
                    if not idx_key:
                        idx_key = self.storage.keys.get(entity['key'])
                    pk = PublicKey(idx_key['bytes'])
                else:
                    pk = None
                return Profile(entity, pk)

    def put(self, profile):
        entity = {k: v for k, v in vars(profile).items()
                  if not k.startswith('_')}
        self.storage.profiles.put(entity)
        profile.id = entity['id']

        if 'name' in profile._changes:
            old, new = profile._changes['name'], profile.name
            if old:
                self.storage.profile_names.delete(old)
            self.storage.profile_names.put(dict(id=new, profile_id=profile.id))

        if 'key' in profile._changes:
            old, new = profile._changes['key'], profile.key
            if old:
                self.storage.keys.delete(old.hash)
            self.storage.keys.put(dict(id=new.hash, bytes=new.encode(),
                                       profile_id=profile.id))

        if 'hook' in profile._changes:
            old, new = profile._changes['hook'], profile.hook
            if old:
                old_id = hashlib.sha1(old.encode()).hexdigest()
                self.storage.hooks.delete(old_id)
            new_id = hashlib.sha1(new.encode()).hexdigest()
            self.storage.hooks.put(dict(id=new_id, profile_id=profile.id))

    def parse_blocks(self, blocks, verify=True):
        r = Blocks({})
        required_keys = self._BLOCK_REQUIRED_KEYS
        valid_keys = required_keys | self._BLOCK_OPTIONAL_KEYS
        for signature, block_ in blocks.items():
            included = block_.keys() & required_keys
            if included != required_keys:
                keys = ', '.join(required_keys - included)
                raise ValueError(f"missing required keys: {keys}")
            invalid_keys = block_.keys() - valid_keys
            if invalid_keys:
                keys = ', '.join(invalid_keys)
                raise ValueError(f"invalid keys: {keys}")
            block = Block()
            by = self.storage.keys.get(block_['by'])
            if not by:
                raise ValueError(f"not registered: {block_['by']}")
            to = self.storage.keys.get(block_['to'])
            if not to:
                raise ValueError(f"not registered: {block_['to']}")
            block.by = PublicKey(by['bytes'])
            block.to = PublicKey(to['bytes'])
            block.data = block_['data']
            signed = block.data.get('signed')
            if isinstance(signed, str):
                block.data['signed'] = datetime.datetime.fromisoformat(signed)
            block.signature = base58decode(signature)
            r.add(block, verify)
        return r


if __name__ == '__main__':
    import argparse
    import pathlib
    import sys
    from . import SecretKey

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command', required=True)

    subparser = subparsers.add_parser('sign')
    subparser.add_argument('--secret-key', type=pathlib.Path, required=True)
    subparser.add_argument('--output', type=str, default='yaml')
    subparser.add_argument('data', type=pathlib.Path, nargs='?')

    subparser = subparsers.add_parser('verify')
    subparser.add_argument('--public-key', type=pathlib.Path, required=True)
    subparser.add_argument('data', type=pathlib.Path, nargs='?')

    args = parser.parse_args()

    if args.command == 'sign':
        sk = SecretKey(args.secret_key.read_bytes())
        data = args.data.read_bytes() if args.data else sys.stdin.buffer.read()
        block = yaml.safe_load(data)
        if block['by'] != sk.public_key.hash:
            print('Error: Invalid signer, fix the "by" in file.',
                  file=sys.stderr)
            exit(1)
        sig = base58encode(sk.sign(Block.serialize(block)))
        blocks = {sig: block}
        if args.output == 'yaml':
            out = yaml.dump(_stringify_yaml(blocks), sort_keys=False).strip()
        else:
            out = json.dumps(blocks, default=_stringify, indent=4)
        print(out)

    if args.command == 'verify':
        pk = PublicKey(args.public_key.read_bytes())
        data = args.data.read_bytes() if args.data else sys.stdin.buffer.read()
        blocks = yaml.safe_load(data)
        for i, (sig, block) in enumerate(blocks.items()):
            if not pk.verify(base58decode(sig), data=Block.serialize(block)):
                print('Error: Invalid signature', sig)
                exit(1)
        print('OK')
