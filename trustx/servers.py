import argparse
import cgi
import datetime
import enum
import html
import io
import json
import random
import re
import threading
import urllib.error
import urllib.parse
import urllib.request

import yaml

from . import (BASE58_CHARACTERS, PublicKey, __version__, base58decode,
               base58encode)
from .profiles import Blocks, Profile, Profiles
from .sessions import HMACSessionFactory, encode_datetime, joinb, splitb


class WSGI:
    statuses = {int(x.split(maxsplit=1)[0]): x.split(maxsplit=1)[1]
                for x in """
200 OK
302 Found
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
405 Method Not Allowed
409 Conflict
""".strip().splitlines()}

    default_headers = [('Access-Control-Allow-Origin', '*')]

    cors_allow_methods = 'DELETE GET OPTIONS POST PUT PATCH'.split()

    route_arg_pattern = re.compile('<([^>]+)>')

    class Request:
        _tl = threading.local()

        @property
        def environ(self):
            return self._tl.environ

        @environ.setter
        def environ(self, value):
            self._tl.environ = value

        @property
        def method(self):
            return self.environ['REQUEST_METHOD']

        @property
        def content_type(self):
            return self.environ['CONTENT_TYPE']

        @property
        def data(self):
            content_length = int(self.environ.get('CONTENT_LENGTH') or 0)
            r = self.environ['wsgi.input'].read(content_length)
            self.environ['wsgi.input'] = io.BytesIO(r)
            self.environ['wsgi.input'].seek(0)
            return r

        @property
        def form(self):
            fp = io.BytesIO(self.data)
            form = cgi.FieldStorage(fp=fp, environ=self.environ)
            return {k: form[k].value for k in form}

        @property
        def args(self):
            args = urllib.parse.parse_qs(self.environ['QUERY_STRING'])
            return {k: html.escape(v[-1]) for k, v in args.items()}

    request = Request()

    def __init__(self):
        self._handlers = []

    def _respond(self, respond, status, headers=None):
        respond(f'{status} {self.statuses[status]}',
                self.default_headers + (headers or []))

    def __call__(self, environ, respond):
        self.request.environ = environ
        route_parts = environ['PATH_INFO'].split('/')
        n_route_parts = len(route_parts)
        for route, f, options in self._handlers:
            route_parts_ = route.split('/')
            if len(route_parts_) != n_route_parts:
                continue
            route_part_matches = []
            route_args = {}
            for a, b in zip(route_parts, route_parts_):
                m = self.route_arg_pattern.match(b)
                if m:
                    route_args[m.group(1)] = a
                    route_part_match = True
                else:
                    route_part_match = a == b
                route_part_matches.append(route_part_match)
            if not all(route_part_matches):
                continue
            method = environ['REQUEST_METHOD'].upper()
            handler_methods = options.get('methods', ['GET'])
            if method not in handler_methods:
                if method == 'OPTIONS' and options.get('cors', True):
                    allow_methods = ', '.join(self.cors_allow_methods)
                    self._respond(respond, 200, [
                        ('Allow', allow_methods),
                        ('Access-Control-Allow-Methods', allow_methods),
                        ('Access-Control-Allow-Headers', 'Authorization')
                    ])
                    return []
                continue

            resp = f(**dict(route_args))
            if isinstance(resp, (list, tuple)):
                content, status = resp[:2]
                headers = resp[2] if len(resp) >= 3 else []
            else:
                content, status, headers = resp, 200, []
            self._respond(respond, status, headers)
            return [(content or '').encode()]
        self._respond(respond, 404)
        return []

    def route(self, route, **options):
        def decorator(f):
            self._handlers.append((route, f, options))
            return f
        return decorator

    @property
    def storage(self):
        if hasattr(self, '_storage'):
            return self._storage
        this = self.__class__.__name__
        raise AttributeError(f"'{this}' object has no attribute 'storage'")

    @storage.setter
    def storage(self, value):
        self._storage = value

    @property
    def session(self):
        if hasattr(self, '_session'):
            return self._session
        this = self.__class__.__name__
        raise AttributeError(f"'{this}' object has no attribute 'session'")

    @session.setter
    def session(self, value):
        self._session = value


wsgi = WSGI()


def post(url, **kwargs):
    headers = {'User-Agent': 'TrustX/' + __version__}
    if 'json' in kwargs:
        data = json.dumps(kwargs['json']).encode()
        headers['Content-Type'] = 'application/json'
    elif 'data' in kwargs:
        data = kwargs['data']
    else:
        data = None
    req = urllib.request.Request(url, data, headers, method='POST')
    try:
        with urllib.request.urlopen(req) as res:
            return True
    except urllib.error.HTTPError:
        pass
    return False


@wsgi.route('/')
def index():
    print(wsgi.request.args)
    return 'Hello!'


@wsgi.route('/a/<b>/c')
def abc(b):
    return str(b)


def get_key_from_request():
    key = wsgi.request.form.get('key')
    return PublicKey(key) if key else None


class PasswordHintType(enum.IntEnum):
    HOOK = enum.auto()
    PROFILE = enum.auto()

    def encode(self):
        return self.to_bytes(1, 'big')


SHORT = datetime.timedelta(hours=1)
LONG = datetime.timedelta(days=3)


@wsgi.route('/passwords', methods=['POST'])
def post_password():
    profile_query = None
    hook = None
    key = get_key_from_request()
    if key:
        profile_query = dict(key=key)
    if not profile_query:
        name = wsgi.request.form.get('name')
        if name:
            profile_query = dict(name=name)
    if not profile_query:
        hook = wsgi.request.form.get('hook')
        if hook:
            profile_query = dict(hook=hook)
    if not profile_query:
        return '', 400
    profiles = Profiles(wsgi.storage)
    profile = profiles.get(**profile_query)
    if profile:
        hook = profile.hook
        hint_type = PasswordHintType.PROFILE.encode()
        hint_data = bytes.fromhex(profile.id)
    elif not hook:
        return '', 403
    else:
        hint_type = PasswordHintType.HOOK.encode()
        hint_data = hook.encode()
    password = ''.join(random.choices(BASE58_CHARACTERS, k=8))
    session = wsgi.session(hint_type, hint_data, password.encode(), life=SHORT)
    expires = encode_datetime(session.expires)
    hint = base58encode(joinb(session.sign, expires, hint_type, hint_data))
    if post(hook, json={'text': password}):
        return json.dumps(hint)
    return '', 400


@wsgi.route('/nonces', methods=['POST'])
def post_nonce():
    key = get_key_from_request()
    if key:
        session = wsgi.session(key.encode(), life=SHORT)
        return json.dumps(session.token)
    return '', 400


@wsgi.route('/tokens', methods=['POST'])
def post_token():
    hint = WSGI.request.form.get('hint')
    password = WSGI.request.form.get('password')
    if hint and password:
        sign, expires, hint_type, hint_data = splitb(base58decode(hint))
        if int.from_bytes(hint_type, 'big') != PasswordHintType.PROFILE:
            return '', 403
        token = joinb(sign, expires, hint_type, hint_data, password.encode())
        if not wsgi.session.parse(base58encode(token)):
            return '', 403
        profile_id = hint_data
    else:
        nonce = WSGI.request.form.get('nonce')
        signature = WSGI.request.form.get('signature')
        if not nonce or not signature:
            return '', 400
        if isinstance(signature, str):
            signature = base58decode(signature)
        nonce_session = wsgi.session.parse(nonce)
        if not nonce_session:
            return '', 403
        key = PublicKey(nonce_session.data[0])
        if not key.verify(signature, data=nonce.encode()):
            return '', 403
        profile_id = bytes.fromhex(Profiles(wsgi.storage).get(key=key).id)
    return json.dumps(wsgi.session(profile_id, life=LONG).token)


@wsgi.route('/profiles', methods=['POST'])
def post_profile():
    hint = wsgi.request.form.get('hint')
    password = wsgi.request.form.get('password')
    name = wsgi.request.form.get('name')
    if not hint or not password or not name:
        return '', 400
    symbols = '-._'
    digits = '0123456789'
    letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    allowed = symbols + digits + letters
    if name[0] in digits or set(name) - set(allowed):
        return '', 400
    sign, expires, hint_type, hint_data = splitb(base58decode(hint))
    if int.from_bytes(hint_type, 'big') != PasswordHintType.HOOK:
        return '', 403
    token = joinb(sign, expires, hint_type, hint_data, password.encode())
    if not wsgi.session.parse(base58encode(token)):
        return '', 403
    hook = hint_data.decode()
    profiles = Profiles(wsgi.storage)
    other = profiles.get(hook=hook)
    if other:
        return '', 409
    other = profiles.get(name=name)
    if other:
        return '', 409
    me = Profile()
    me.name = name
    me.hook = hook
    profiles.put(me)
    token = wsgi.session(bytes.fromhex(me.id), life=LONG).token
    return json.dumps(dict(**vars(me), **dict(token=token)))


class HTTPError(Exception):
    def __init__(self, status, *args, **kwargs):
        self.status = status
        super().__init__(*args, **kwargs)


def get_profile_from_token():
    token = wsgi.request.args.get('token', wsgi.request.form.get('token'))
    if not token:
        raise HTTPError(400)
    session = wsgi.session.parse(token)
    if not session:
        raise HTTPError(403)
    return Profiles(wsgi.storage).get(id=session.data[0].hex())


def stringify(value):
    if isinstance(value, bytes):
        return base58encode(value)
    if isinstance(value, datetime.datetime):
        return value.isoformat()
    return value


def block_details(block_dict):
    r = block_dict.copy()
    r['by'] = dict(base58=r['by'], hash=PublicKey(r['by']).hash)
    r['to'] = dict(base58=r['to'], hash=PublicKey(r['to']).hash)
    return r


def jsonify(obj):
    d = vars(obj).copy()
    if isinstance(obj, Profile) and 'blocks' in d:
        d['blocks'] = {base58encode(k): block_details(v)
                       for k, v in d['blocks'].items()}
    elif isinstance(obj, Blocks):
        d = {base58encode(k): block_details(v) for k, v in d.items()}
    d = {k: v for k, v in d.items() if not k.startswith('_')}
    return json.dumps(d, default=stringify)


@wsgi.route('/profiles/<name_or_keyhash>')
def get_profile(name_or_keyhash):
    try:
        me = get_profile_from_token()
    except HTTPError as e:
        return '', e.status
    if me.name == name_or_keyhash or name_or_keyhash == 'me':
        return jsonify(me)
    profiles = Profiles(wsgi.storage)
    other = profiles.get(name=name_or_keyhash)
    if not other:
        other = profiles.get(hash=name_or_keyhash)
    if other:
        other = {k: v for k, v in vars(other).items() if k in ('id', 'name')}
        return jsonify(other)


@wsgi.route('/profiles/<name_or_keyhash>/key', methods=['PUT'])
def put_profile_key(name_or_keyhash):
    try:
        me = get_profile_from_token()
    except HTTPError as e:
        return '', e.status
    if me.name != name_or_keyhash and name_or_keyhash != 'me':
        return '', 403
    nonce = WSGI.request.form.get('nonce')
    signature = WSGI.request.form.get('signature')
    if not nonce or not signature:
        return '', 400
    if isinstance(signature, str):
        signature = base58decode(signature)
    nonce_session = wsgi.session.parse(nonce)
    if not nonce_session:
        return '', 403
    key = PublicKey(nonce_session.data[0])
    if not key.verify(signature, data=nonce.encode()):
        return '', 403
    profiles = Profiles(wsgi.storage)
    other = profiles.get(key=key)
    if other:
        return '', 409
    me.key = key
    profiles.put(me)
    return jsonify(me)


@wsgi.route('/profiles/<name_or_keyhash>/name', methods=['PUT'])
def put_profile_name(name_or_keyhash):
    try:
        me = get_profile_from_token()
    except HTTPError as e:
        return '', e.status
    if me.name != name_or_keyhash and name_or_keyhash != 'me':
        return '', 403
    name = wsgi.request.form.get('name')
    if not name:
        return '', 400
    profiles = Profiles(wsgi.storage)
    other = profiles.get(name=name)
    if other:
        return '', 409
    me.name = name
    profiles.put(me)
    return jsonify(me)


@wsgi.route('/profiles/<name_or_keyhash>/hook', methods=['PUT'])
def put_profile_hook(name_or_keyhash):
    try:
        me = get_profile_from_token()
    except HTTPError as e:
        return '', e.status
    if me.name != name_or_keyhash and name_or_keyhash != 'me':
        return '', 403
    hint = wsgi.request.form.get('hint')
    password = wsgi.request.form.get('password')
    if not hint or not password:
        return '', 400
    sign, expires, hint_type, hint_data = splitb(base58decode(hint))
    if int.from_bytes(hint_type, 'big') != PasswordHintType.HOOK:
        return '', 403
    token = joinb(sign, expires, hint_type, hint_data, password.encode())
    if not wsgi.session.parse(base58encode(token)):
        return '', 403
    hook = hint_data.decode()
    profiles = Profiles(wsgi.storage)
    other = profiles.get(hook=hook)
    if other:
        return '', 409
    me.hook = hook
    profiles.put(me)
    return jsonify(me)


@wsgi.route('/profiles/<name_or_keyhash>/blocks', methods=['PUT'])
def put_profile_blocks(name_or_keyhash):
    try:
        me = get_profile_from_token()
    except HTTPError as e:
        return '', e.status
    if me.name != name_or_keyhash and name_or_keyhash != 'me':
        return '', 403
    if not me.key:
        return '', 403
    blocks = wsgi.request.form.get('blocks')
    if not blocks:
        return '', 400
    blocks = Blocks.parse(yaml.safe_load(blocks))
    me.blocks.update(blocks)
    Profiles(wsgi.storage).put(me)
    return jsonify(blocks)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='type', required=True)
    subparser = subparsers.add_parser('wsgi')
    subparser.add_argument('--port', default=8000)
    args = parser.parse_args()
    if args.type == 'wsgi':
        import os
        import wsgiref.simple_server
        from .storages import LocalStorage
        wsgi.storage = LocalStorage()
        secret = os.environ['TRUSTX_SESSION_SECRET'].encode('utf-8')
        wsgi.session = HMACSessionFactory(secret)
        with wsgiref.simple_server.make_server('', args.port, wsgi) as httpd:
            print(f'Serving HTTP on port {args.port}, control-C to stop')
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print('Shutting down.')
