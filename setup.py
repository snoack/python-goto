from setuptools import setup

setup(
    name='goto-statement',
    version='1.1',
    url='https://github.com/snoack/python-goto/',
    description='A function decorator, that rewrites the bytecode, to enable goto in Python',
    py_modules=['goto'],
    author='Sebastian Noack',
    author_email='sebastian.noack@gmail.com',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: Public Domain',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
