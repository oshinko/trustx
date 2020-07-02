import datetime
import hmac

from . import base58decode, base58encode, hashfunc


def encode_to_7bit(value):
    """
    Encode unsigned int to 7-bit str data
    """
    data = []
    number = abs(value)
    while number >= 0x80:
        data.append((number | 0x80) & 0xff)
        number >>= 7
    data.append(number & 0xff)
    return bytes(data)


def decode_from_7bit(data):
    """
    Decode 7-bit encoded int from str data
    """
    decoded = 0
    n_consumed = 0
    for index, byte in enumerate(data):
        decoded |= (byte & 0x7f) << (7 * index)
        n_consumed += 1
        if byte & 0x80 == 0:
            break
    return decoded, n_consumed


def joinb(*args):
    return b''.join(encode_to_7bit(len(x)) + x for x in args)


def splitb(data):
    while data:
        length, n_consumed = decode_from_7bit(data)
        s, e = n_consumed, n_consumed + length
        yield data[s:e]
        data = data[e:]


def encode_datetime(value):
    return int(value.timestamp()).to_bytes(8, 'big').lstrip(b'\0')


def decode_datetime(data):
    return datetime.datetime.fromtimestamp(int.from_bytes(data, 'big'))


class HMACSessionFactory:
    def __init__(self, secret, now=None, life=None):
        self.secret = secret
        self.now = now if now else datetime.datetime.now
        self.life = life if life else datetime.timedelta(days=1)

    def __call__(self, *data, life=None):
        r = Session()
        r.now = self.now
        r.data = data
        r.expires = self.now() + (life or self.life)
        expires = encode_datetime(self.now() + (life or self.life))
        r.expires = decode_datetime(expires)
        message = expires + b''.join(r.data)
        r.sign = hmac.new(self.secret, message, hashfunc).digest()
        r.valid = True
        r.token = base58encode(joinb(r.sign, expires, *r.data))
        return r

    def parse(self, token):
        r = Session()
        r.now = self.now
        r.token = token
        try:
            token = base58decode(r.token)
            r.sign, expires, *data = splitb(token)
            ts = int.from_bytes(expires, 'big')
            r.expires = datetime.datetime.fromtimestamp(ts)
            r.data = tuple(data)
            message = expires + b''.join(r.data)
            sign = hmac.new(self.secret, message, hashfunc)
            r.valid = r.sign == sign.digest()
        except Exception:
            pass
        return r


class Session:
    valid = False

    def __bool__(self):
        return self.valid and self.expires > self.now()

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False
