import argparse
import pathlib
import sys

import base58
import ecdsa

from . import curve, get_address_from_verifying_key, hashfunc

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest='command', required=True)

gen_parser = subparsers.add_parser('gen')
gen_parser.add_argument('--signing-key', type=pathlib.Path)
gen_parser.add_argument('--verifying-key', type=pathlib.Path)

concat_parser = subparsers.add_parser('concat')
concat_parser.add_argument('data', type=pathlib.Path, nargs='+')

sign_parser = subparsers.add_parser('sign')
sign_parser.add_argument('--signing-key', type=pathlib.Path, required=True)
sign_parser.add_argument('data', type=pathlib.Path, nargs='?')

verify_parser = subparsers.add_parser('verify')
verify_parser.add_argument('--verifying-key', type=pathlib.Path, required=True)
verify_parser.add_argument('--data', type=pathlib.Path, required=True)
verify_parser.add_argument('signature', type=pathlib.Path, nargs='?')

addr_parser = subparsers.add_parser('addr')
addr_parser.add_argument('--signing-key', type=pathlib.Path)
addr_parser.add_argument('--verifying-key', type=pathlib.Path)
addr_parser.add_argument('--encoding', default='compressed')

hex_parser = subparsers.add_parser('hex')
hex_parser.add_argument('data', type=pathlib.Path, nargs='?')

base58_parser = subparsers.add_parser('base58')
base58_parser.add_argument('data', type=pathlib.Path, nargs='?')

args = parser.parse_args()

if args.command == 'gen':
    if not args.signing_key and not args.verifying_key:
        parser.error('No keys requested, add --signing-key or --verifying-key')
    sk = ecdsa.SigningKey.generate(curve, hashfunc=hashfunc)
    assert sk == ecdsa.SigningKey.from_string(sk.to_string(), curve, hashfunc)
    if args.signing_key:
        args.signing_key.write_bytes(sk.to_string())
    if args.verifying_key:
        vk = sk.verifying_key
        args.verifying_key.write_bytes(vk.to_string('compressed'))

if args.command == 'concat':
    sys.stdout.buffer.write(b''.join(x.read_bytes() for x in args.data))

if args.command == 'sign':
    sk_str = args.signing_key.read_bytes()
    sk = ecdsa.SigningKey.from_string(sk_str, curve, hashfunc)
    data = args.data.read_bytes() if args.data else sys.stdin.buffer.read()
    sys.stdout.buffer.write(sk.sign(data))

if args.command == 'verify':
    vk_str = args.verifying_key.read_bytes()
    vk = ecdsa.VerifyingKey.from_string(vk_str, curve, hashfunc)
    if args.signature:
        sig = args.signature.read_bytes()
    else:
        sig = sys.stdin.buffer.read()
    vk.verify(sig, args.data.read_bytes())
    print('OK')

if args.command == 'addr':
    if not args.signing_key and not args.verifying_key:
        parser.error('No keys requested, add --signing-key or --verifying-key')
    if args.signing_key:
        sk_str = args.signing_key.read_bytes()
        sk = ecdsa.SigningKey.from_string(sk_str, curve, hashfunc)
        vk = sk.verifying_key
    else:
        vk_str = args.verifying_key.read_bytes()
        vk = ecdsa.VerifyingKey.from_string(vk_str, curve, hashfunc)
    print(get_address_from_verifying_key(vk, encoding=args.encoding))

if args.command == 'hex':
    data = args.data.read_bytes() if args.data else sys.stdin.buffer.read()
    print(data.hex())

if args.command == 'base58':
    data = args.data.read_bytes() if args.data else sys.stdin.buffer.read()
    print(base58.b58encode(data).decode('ascii'))
