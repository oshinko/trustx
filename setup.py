from setuptools import setup

setup(
    name='trustx',
    version='0.0.0',
    description='Signable profile exchange network service.',
    author='Oshinko',
    author_email='osnk@renjaku.jp',
    url='https://github.com/maesin/trustx',
    install_requires=['base58', 'ecdsa'],
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython'
    ]
)
