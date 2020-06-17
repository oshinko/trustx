import datetime
import hmac

import base58

from . import hashfunc


def now():
    return datetime.datetime.now()


def expires():
    return now() + datetime.timedelta(days=3)


class HMACSessionBuilder:
    def __init__(self, secret):
        self.secret = secret

    def __call__(self, *data_or_token):
        r = Session()
        if len(data_or_token) == 1 and isinstance(data_or_token[0], str):
            r.token = data_or_token[0]
            try:
                token = base58.b58decode(r.token)
                i = 0
                parts = []
                while i < len(token):
                    length = token[i]
                    j = i + 1
                    i = j + length
                    parts.append(token[j:i])
                r.sign, ebin, *data = parts
                ts = int.from_bytes(ebin, 'big')
                r.expires = datetime.datetime.fromtimestamp(ts)
                r.data = tuple(data)
                message = ebin + b''.join(r.data)
                sign = hmac.new(self.secret, message, hashfunc)
                r.valid = r.sign == sign.digest()
            except Exception:
                pass
        else:
            r.data = data_or_token
            r.expires = expires()
            ebin = int(r.expires.timestamp()).to_bytes(8, 'big')
            ebin = ebin.lstrip(b'\0')
            message = ebin + b''.join(r.data)
            r.sign = hmac.new(self.secret, message, hashfunc).digest()
            r.valid = True
            token = bytearray()
            token.extend(len(r.sign).to_bytes(1, 'big'))
            token.extend(r.sign)
            token.extend(len(ebin).to_bytes(1, 'big'))
            token.extend(ebin)
            for x in r.data:
                token.extend(len(x).to_bytes(1, 'big'))
                token.extend(x)
            r.token = base58.b58encode(token).decode()
        return r


class Session:
    expires = datetime.datetime.min
    valid = False

    def __bool__(self):
        return self.valid and self.expires > now()
