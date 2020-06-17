
import json
import sys

import base58
import ecdsa

from .. import curve, get_address_from_verifying_key, hashfunc
from ..sessions import HMACSessionBuilder

secret = b'Replace this with your secret'
Session = HMACSessionBuilder(secret)


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self


class Handlers(dict):
    def __call__(self, *args):
        method, *uri_and_params = args
        if ' ' in method:
            method, uri = method.split(' ', 1)
            params = uri_and_params
        else:
            uri, *params = uri_and_params
        method = method.upper()
        params_ = []
        for param in params:
            if param.startswith('-'):
                params_.append((param.strip('-'),))
            else:
                params_[-1] += param,
        params__ = {}
        for k, *v in params_:
            if v:
                params__[k] = v[0] if len(v) == 1 else v
            else:
                params__[k] = True
            params__[k.replace('-', '_')] = params__[k]
        resp = self[method, uri](AttrDict(params__))
        if isinstance(resp, (list, tuple)):
            status, content = resp
        else:
            status, content = 200, resp
        if isinstance(content, dict):
            content = json.dumps(content, indent=4)
        if isinstance(content, str):
            content = content.encode('utf-8')
        return status, content


handlers = Handlers()


def route(method, uri):
    def decorate(f):
        handlers[method, uri] = f
        return f
    return decorate


@route('GET', '/auth/nonce')
def get_auth_nonce(params):
    return Session(base58.b58decode(params.verifying_key)).token


@route('GET', '/auth/token')
def get_auth_token(params):
    session = Session(params.nonce)
    if session:
        signature = base58.b58decode(params.signature)
        vk_str = session.data[0]
        vk = ecdsa.VerifyingKey.from_string(vk_str, curve, hashfunc)
        try:
            vk.verify(signature, params.nonce.encode())
        except ecdsa.BadSignatureError:
            return 401, dict(error='Invalid nonce')
        else:
            return Session(vk_str).token
    return 401, dict(error='Invalid nonce')


@route('GET', '/profiles/me')
def get_my_profile(params):
    session = Session(params.token)
    if session:
        vk = ecdsa.VerifyingKey.from_string(session.data[0], curve, hashfunc)
        return dict(address=get_address_from_verifying_key(vk))
    return 401, dict(error='Invalid token')


status, response = handlers(*sys.argv[1:])
sys.stdout.buffer.write(response)
exit(0 if status == 200 else status)
