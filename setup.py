from pathlib import Path

from setuptools import setup

name = 'trustx'

with (Path(__file__).parent / name / '__init__.py').open() as f:
    for line in f:
        if line.startswith('__version__'):
            _, value = (x for x in line.split('=', 2))
            version = str(eval(value))
            break
    else:
        raise RuntimeError('Unable to find version string.')

setup(
    name=name,
    version=version,
    description='Signable profile exchange network service.',
    author='Oshinko',
    author_email='osnk@renjaku.jp',
    url='https://github.com/oshinko/trustx',
    packages=[name],
    install_requires=Path('requirements.txt').read_text().split(),
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython'
    ]
)
