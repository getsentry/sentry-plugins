#!/usr/bin/env python
"""
sentry-plugins
==============

All of the plugins for Sentry (https://github.com/getsentry/sentry)

:copyright: 2019 by the Sentry Team
:license: BSL-1.1, see LICENSE for more details.
"""
from __future__ import absolute_import

from distutils.command.build import build as BuildCommand
from setuptools import setup, find_packages
from setuptools.command.sdist import sdist as SDistCommand
from setuptools.command.develop import develop as DevelopCommand

from sentry.utils.distutils import BuildAssetsCommand

VERSION = "10.0.0.dev0"

tests_require = [
    "exam>=0.5.1",
    "responses>=0.8.1,<0.9.0",
    "pytest==4.6.5",
    "pytest-cov==2.5.1",
    "pytest-django==3.5.1",
    "pytest-html==1.22.0",
    "sentry>=8.9.0",
    "sentry-flake8==0.1.1",
]

# Any dependencies pinned here should be subdependencies of sentry that are
# explicitly used (as in imported) by sentry-plugins.
# For the most part, the pins should be the same and synced with each other.
install_requires = [
    "BeautifulSoup>=3.2.1",
    "boto3>=1.4.4,<1.5.0",
    "djangorestframework==3.4.7",
    "mistune>0.7,<0.9",
    "python-dateutil>=2.0.0,<3.0.0",
    "PyJWT>=1.5.0,<1.6.0",
    "requests-oauthlib==0.3.3",
    "unidiff>=0.5.4",
    # below this line are sentry-plugins specific dependencies
    "cached-property",
    "phabricator>=0.6.0,<1.0",
]


class BuildAssetsCommand(BuildAssetsCommand):
    def get_dist_paths(self):
        return []


class SentrySDistCommand(SDistCommand):
    sub_commands = SDistCommand.sub_commands + [("build_assets", None)]

    def run(self):
        SDistCommand.run(self)


class SentryBuildCommand(BuildCommand):
    def run(self):
        BuildCommand.run(self)


class SentryDevelopCommand(DevelopCommand):
    def run(self):
        DevelopCommand.run(self)


cmdclass = {
    "sdist": SentrySDistCommand,
    "develop": SentryDevelopCommand,
    "build": SentryBuildCommand,
    "build_assets": BuildAssetsCommand,
}

setup(
    name="sentry-plugins",
    version=VERSION,
    author="Sentry",
    author_email="hello@sentry.io",
    url="https://github.com/getsentry/sentry-plugins",
    description="A collection of Sentry extensions",
    long_description=__doc__,
    license="BSL-1.1",
    package_dir={"": "src"},
    packages=find_packages("src"),
    zip_safe=False,
    cmdclass=cmdclass,
    install_requires=install_requires,
    extras_require={"tests": tests_require},
    include_package_data=True,
    entry_points={"sentry.plugins": []},
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Operating System :: OS Independent",
        "Topic :: Software Development",
        "License :: Other/Proprietary License",
    ],
)
