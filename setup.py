#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# pacifica-dispatcher-proxymod: setup.py
#
# Copyright (c) 2019, Battelle Memorial Institute
# All rights reserved.
#
# See LICENSE and WARRANTY for details.

try:
    from pip.req import parse_requirements
except ImportError:
    from pip._internal.req import parse_requirements
from setuptools import setup, find_packages

INSTALL_REQS = parse_requirements('requirements.txt', session='hack')

setup(
    name='pacifica-dispatcher-proxymod',
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    description='Pacifica Dispatcher for proxymod',
    author='Mark Borkum',
    author_email='mark.borkum@pnnl.gov',
    packages=find_packages(),
    namespace_packages=['pacifica'],
    entry_points={
        'console_scripts': [
            'pacifica-dispatcher-proxymod=pacifica.dispatcher.proxymod.__main__:main',
        ],
    },
    install_requires=[str(ir.req) for ir in INSTALL_REQS]
)
