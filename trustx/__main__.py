import argparse
import pathlib
import sys

import yaml

from . import PublicKey, SecretKey, base58encode

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest='command', required=True)

subparser = subparsers.add_parser('gen')
subparser.add_argument('--secret-key', type=pathlib.Path)
subparser.add_argument('--public-key', type=pathlib.Path)

subparser = subparsers.add_parser('concat')
subparser.add_argument('data', type=pathlib.Path, nargs='+')

subparser = subparsers.add_parser('sign')
subparser.add_argument('--secret-key', type=pathlib.Path, required=True)
subparser.add_argument('data', type=pathlib.Path, nargs='?')

subparser = subparsers.add_parser('verify')
subparser.add_argument('--public-key', type=pathlib.Path, required=True)
subparser.add_argument('--data', type=pathlib.Path, required=True)
subparser.add_argument('signature', type=pathlib.Path, nargs='?')

subparser = subparsers.add_parser('hash')
subparser.add_argument('--secret-key', type=pathlib.Path)
subparser.add_argument('--public-key', type=pathlib.Path)

subparser = subparsers.add_parser('hex')
subparser.add_argument('data', type=pathlib.Path, nargs='?')

subparser = subparsers.add_parser('base58')
subparser.add_argument('data', type=pathlib.Path, nargs='?')

subparser = subparsers.add_parser('yaml')
subparser.add_argument('data', type=pathlib.Path, nargs='?')

args = parser.parse_args()

if args.command == 'gen':
    if not args.secret_key and not args.public_key:
        parser.error('No keys requested, add --secret-key or --public-key')
    sk = SecretKey()
    assert sk == SecretKey(sk.encode())
    if args.secret_key:
        args.secret_key.write_bytes(sk.to_string())
    if args.public_key:
        vk = sk.public_key
        args.public_key.write_bytes(vk.to_string('compressed'))

if args.command == 'concat':
    sys.stdout.buffer.write(b''.join(x.read_bytes() for x in args.data))

if args.command == 'sign':
    sk = SecretKey(args.secret_key.read_bytes())
    data = args.data.read_bytes() if args.data else sys.stdin.buffer.read()
    sys.stdout.buffer.write(sk.sign(data))

if args.command == 'verify':
    pk = PublicKey(args.public_key.read_bytes())
    if args.signature:
        sig = args.signature.read_bytes()
    else:
        sig = sys.stdin.buffer.read()
    pk.verify(sig, data=args.data.read_bytes())
    print('OK')

if args.command == 'hash':
    if not args.secret_key and not args.public_key:
        parser.error('No keys requested, add --secret-key or --public-key')
    if args.secret_key:
        sk = SecretKey(args.secret_key.read_bytes())
        pk = sk.public_key
    else:
        pk = PublicKey(args.public_key.read_bytes())
    print(pk.hash)

if args.command == 'hex':
    data = args.data.read_bytes() if args.data else sys.stdin.buffer.read()
    print(data.hex())

if args.command == 'base58':
    data = args.data.read_bytes() if args.data else sys.stdin.buffer.read()
    print(base58encode(data))

if args.command == 'yaml':
    data = args.data.read_bytes() if args.data else sys.stdin.buffer.read()
    print(yaml.dump(yaml.safe_load(data), sort_keys=False).strip())
