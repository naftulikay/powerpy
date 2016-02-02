#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name = "powerpy",
    description = "A slideshow REST API in Python.",
    version = "0.1.0",
    license = "MIT",
    packages = find_packages('src'),
    package_dir = { '': 'src'},
    install_requires = ['setuptools',
        'tornado == 4.3',
        'tornado-redis == 2.4.18',
        'redis == 2.10.5',
        'hiredis == 0.2.0',
        'python-magic >= 0.4.0,<0.5.0',
        'celery == 3.1.20',
        'boto3 == 1.2.3',
    ],
    entry_points = {
        'console_scripts': [
            'powerpy-web = powerpy.web:start_webserver',
            'powerpy-worker = powerpy.worker:start_worker',
        ],
    },
    zip_safe = True
)
