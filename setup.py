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

from distutils.command.build import build as BuildCommand
from setuptools import setup, find_packages
from setuptools.command.sdist import sdist as SDistCommand
from setuptools.command.develop import develop as DevelopCommand

from sentry.utils.distutils import (
    BuildAssetsCommand
)

tests_require = [
    'exam',
    'flake8>=2.0,<2.1',
    'responses',
    'sentry>=8.6.0',
    'pyjwt>=0.3.2',
]

install_requires = [
    'PyJWT',
]


class BuildAssetsCommand(BuildAssetsCommand):
    def get_dist_paths(self):
        return [
            'src/sentry_plugins/hipchat_ac/static/hipchat_ac/dist',
        ]


class SentrySDistCommand(SDistCommand):
    sub_commands = SDistCommand.sub_commands + \
        [('build_assets', None)]

    def run(self):
        cmd_obj = self.distribution.get_command_obj('build_assets')
        cmd_obj.asset_json_path = 'sentry_plugins/assets.json'
        SDistCommand.run(self)


class SentryBuildCommand(BuildCommand):
    def run(self):
        BuildCommand.run(self)
        cmd_obj = self.distribution.get_command_obj('build_assets')
        cmd_obj.asset_json_path = 'sentry_plugins/assets.json'
        self.run_command('build_assets')


class SentryDevelopCommand(DevelopCommand):
    def run(self):
        DevelopCommand.run(self)
        cmd_obj = self.distribution.get_command_obj('build_assets')
        cmd_obj.asset_json_path = 'sentry_plugins/assets.json'
        self.run_command('build_assets')


cmdclass = {
    'sdist': SentrySDistCommand,
    'develop': SentryDevelopCommand,
    'build': SentryBuildCommand,
    'build_assets': BuildAssetsCommand,
}

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
    cmdclass=cmdclass,
    install_requires=install_requires,
    extras_require={'tests': tests_require},
    include_package_data=True,
    entry_points={
        'sentry.apps': [
            'github = sentry_plugins.github',
            'gitlab = sentry_plugins.gitlab',
            'hipchat_ac = sentry_plugins.hipchat_ac',
            'jira_ac = sentry_plugins.jira_ac',
            'pagerduty = sentry_plugins.pagerduty',
            'pivotal = sentry_plugins.pivotal',
        ],
        'sentry.plugins': [
            'github = sentry_plugins.github.plugin:GitHubPlugin',
            'gitlab = sentry_plugins.gitlab.plugin:GitLabPlugin',
            'hipchat_ac = sentry_plugins.hipchat_ac.plugin:HipchatPlugin',
            'jira_ac = sentry_plugins.jira_ac.plugin:JiraACPlugin'
            'pagerduty = sentry_plugins.pagerduty.plugin:PagerDutyPlugin',
            'pivotal = sentry_plugins.pivotal.plugin:PivotalPlugin',
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
