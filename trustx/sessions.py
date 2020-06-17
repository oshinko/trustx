import datetime
import hashlib
import hmac

import base58


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
                data = []
                while i < len(token):
                    length = token[i]
                    j = i + 1
                    i = j + length
                    data.append(token[j:i])
                r.sign = data[0]
                ts = int.from_bytes(data[1], 'big')
                r.expires = datetime.datetime.fromtimestamp(ts)
                r.data = tuple(data[2:])
                sign = hmac.new(secret, data[1] + b''.join(r.data), hashlib.sha256)
                r.valid = r.sign == sign.digest()
            except Exception:
                pass
        else:
            self.data = data_or_token
            self.expires = expires()
            ebin = int(self.expires.timestamp()).to_bytes(8, 'big')
            ebin = ebin.lstrip(b'\0')
            message = ebin + b''.join(self.data)
            self.sign = hmac.new(secret, message, hashlib.sha256).digest()
            self.valid = True
            token = bytearray()
            token.extend(len(self.sign).to_bytes(1, 'big'))
            token.extend(self.sign)
            token.extend(len(ebin).to_bytes(1, 'big'))
            token.extend(ebin)
            for x in self.data:
                token.extend(len(x).to_bytes(1, 'big'))
                token.extend(x)
            self.token = base58.b58encode(token).decode()
        return r


class Session:
    expires = datetime.datetime.min
    valid = False

    def __bool__(self):
        return self.valid and self.expires > now()
