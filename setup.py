#!/usr/bin/env python
"""
sentry-plugins
=============

An extension for Sentry which integrates with GitHub. Specifically, it allows you to easily create
issues from events within Sentry.

:copyright: (c) 2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

from setuptools import setup, find_packages

tests_require = [
    'exam',
    'flake8>=2.0,<2.1',
    'responses',
    'sentry>=8.6.0',
]

install_requires = ['pyvotal>=0.2.1, <0.3.0']

setup(
    name='sentry-plugins',
    version='0.1.2',
    author='David Cramer',
    author_email='dcramer@gmail.com',
    url='http://github.com/getsentry/sentry-plugins',
    description='A collection of Sentry extensions',
    long_description=__doc__,
    license='BSD',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    zip_safe=False,
    install_requires=install_requires,
    extras_require={'tests': tests_require},
    include_package_data=True,
    entry_points={
        'sentry.apps': [
            'github = sentry_plugins.github',
            'pivotal = sentry_plugins.pivotal'
        ],
        'sentry.plugins': [
            'github = sentry_plugins.github.plugin:GitHubPlugin',
            'pivotal = sentry_plugins.pivotal.plugin:PivotalPlugin'
        ],
    },
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: Software Development'
    ],
)
