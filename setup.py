import os
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as file:
    long_description = file.read()

setup(
    name='goto-statement',
    version='1.2',
    url='https://github.com/snoack/python-goto/',
    description='A function decorator, that rewrites the bytecode, to enable goto in Python',
    long_description=long_description,
    long_description_content_type='text/markdown',
    py_modules=['goto'],
    author='Sebastian Noack',
    author_email='sebastian.noack@gmail.com',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: Public Domain',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
