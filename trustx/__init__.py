import hashlib

import base58 as b58
import ecdsa

__version__ = '0.0.0'

CURVE = ecdsa.SECP256k1
hashfunc = hashlib.sha256

BASE58_CHARACTERS = b58.BITCOIN_ALPHABET.decode()


def base58encode(data, alphabet=BASE58_CHARACTERS.encode(), returns=str):
    base58 = b58.b58encode(data, alphabet)
    return base58.decode() if returns == str else base58


def base58decode(base58, alphabet=BASE58_CHARACTERS.encode()):
    return b58.b58decode(base58, alphabet)


class SecretKey:
    def __init__(self, source=None):
        if source:
            if isinstance(source, (bytearray, bytes)):
                self._sk = ecdsa.SigningKey.from_string(source, CURVE,
                                                        hashfunc)
            elif isinstance(source, str):
                s = base58decode(source)
                self._sk = ecdsa.SigningKey.from_string(s, CURVE, hashfunc)
            else:
                raise TypeError(('argument should be a str or bytes or None,'
                                 f' not {source.__class__}'))
        else:
            self._sk = ecdsa.SigningKey.generate(CURVE, hashfunc=hashfunc)

    @property
    def public_key(self):
        return PublicKey(self._sk.verifying_key)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False

    def __str__(self):
        return base58encode(self.encode())

    def encode(self):
        return self._sk.to_string()

    def sign(self, data):
        return self._sk.sign(data)


class PublicKey:
    def __init__(self, source):
        if isinstance(source, (bytearray, bytes)):
            self._vk = ecdsa.VerifyingKey.from_string(source, CURVE, hashfunc)
        elif isinstance(source, str):
            s = base58decode(source)
            self._vk = ecdsa.VerifyingKey.from_string(s, CURVE, hashfunc)
        else:
            self._vk = source

    @property
    def hash(self):
        rip = hashlib.new('ripemd160', hashfunc(self.encode()).digest())
        keyhash = b'\0' + rip.digest()
        checksum = hashfunc(hashfunc(keyhash).digest()).digest()[:4]
        return base58encode(keyhash + checksum)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False

    def __hash__(self):
        return hash(self.encode())

    def __str__(self):
        return base58encode(self.encode())

    def encode(self):
        return self._vk.to_string('compressed')

    def verify(self, signature, *, data):
        try:
            return self._vk.verify(signature, data)
        except ecdsa.BadSignatureError:
            return False
