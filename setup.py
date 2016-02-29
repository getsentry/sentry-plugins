#!/usr/bin/env python
"""
sentry-github
=============

An extension for Sentry which integrates with GitHub. Specifically, it allows you to easily create
issues from events within Sentry.

:copyright: (c) 2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from setuptools import setup, find_packages


tests_require = [
    'exam',
    'flake8>=2.0,<2.1',
    'responses',
]

install_requires = [
    'sentry>=7.0.0',
]

setup(
    name='sentry-github',
    version='0.1.2',
    author='David Cramer',
    author_email='dcramer@gmail.com',
    url='http://github.com/getsentry/sentry-github',
    description='A Sentry extension which integrates with GitHub.',
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
            'github = sentry_github',
        ],
        'sentry.plugins': [
            'github = sentry_github.plugin:GitHubPlugin'
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
