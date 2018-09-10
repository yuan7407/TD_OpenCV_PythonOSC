#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
    setup
    ~~~~~

    Setup Script
    Run the build process by running the command 'python setup.py build'

    :copyright: (c) 2018 by Oleksii Lytvyn.
    :license: MIT, see LICENSE for more details.
"""

import osc.osc as osc

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='osc',
    version=osc.__version__,
    author='Oleksii Lytvyn',
    author_email='grailapplication@gmail.com',
    description='OSC implementation in pure Python',
    long_description=open('README.rst').read(),
    url='https://bitbucket.org/grailapp/osc',
    download_url='https://bitbucket.org/grailapp/osc/get/default.zip',
    platforms='any',
    packages=['osc'],
    keywords=['osc', 'protocol', 'utilities', 'osc-1.0', 'network', 'communication', 'udp'],
    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Multimedia :: Sound/Audio',
        'Topic :: System :: Networking',
        'License :: OSI Approved :: MIT License'
    ],
    install_requires=[]
)
