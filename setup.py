#!/usr/bin/env python
"""
sentry-plugins
==============

All of the plugins for Sentry (https://github.com/getsentry/sentry)

:copyright: 2016 by the Sentry Team, see AUTHORS for more details.
:license: Apache, see LICENSE for more details.
"""
from __future__ import absolute_import

from distutils.command.build import build as BuildCommand
from setuptools import setup, find_packages
from setuptools.command.sdist import sdist as SDistCommand
from setuptools.command.develop import develop as DevelopCommand

from sentry.utils.distutils import (
    BuildAssetsCommand
)

VERSION = '8.12.0'

tests_require = [
    'exam',
    'flake8>=2.0,<2.1',
    'responses',
    'sentry>=8.9.0',
    'pyjwt>=0.3.2',
]

install_requires = [
    'BeautifulSoup>=3.2.1',
    'python-dateutil',
    'PyJWT',
    'requests-oauthlib>=0.3.0'
]


class BuildAssetsCommand(BuildAssetsCommand):
    def get_dist_paths(self):
        return [
            'src/sentry_plugins/hipchat_ac/static/hipchat_ac/dist',
            'src/sentry_plugins/jira/static/jira/dist',
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
    version=VERSION,
    author='Sentry',
    author_email='hello@sentry.io',
    url='https://github.com/getsentry/sentry-plugins',
    description='A collection of Sentry extensions',
    long_description=__doc__,
    license='Apache',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    zip_safe=False,
    cmdclass=cmdclass,
    install_requires=install_requires,
    extras_require={'tests': tests_require},
    include_package_data=True,
    entry_points={
        'sentry.apps': [
            'asana = sentry_plugins.asana',
            'bitbucket = sentry_plugins.bitbucket',
            'github = sentry_plugins.github',
            'gitlab = sentry_plugins.gitlab',
            'hipchat_ac = sentry_plugins.hipchat_ac',
            'jira = sentry_plugins.jira',
            'jira_ac = sentry_plugins.jira_ac',
            'pagerduty = sentry_plugins.pagerduty',
            'pivotal = sentry_plugins.pivotal',
            'pushover = sentry_plugins.pushover',
            'segment = sentry_plugins.segment',
            'slack = sentry_plugins.slack',
            'victorops = sentry_plugins.victorops',
        ],
        'sentry.plugins': [
            'asana = sentry_plugins.asana.plugin:AsanaPlugin',
            'bitbucket = sentry_plugins.bitbucket.plugin:BitbucketPlugin',
            'github = sentry_plugins.github.plugin:GitHubPlugin',
            'gitlab = sentry_plugins.gitlab.plugin:GitLabPlugin',
            'hipchat_ac = sentry_plugins.hipchat_ac.plugin:HipchatPlugin',
            'jira = sentry_plugins.jira.plugin:JiraPlugin',
            'jira_ac = sentry_plugins.jira_ac.plugin:JiraACPlugin',
            'pagerduty = sentry_plugins.pagerduty.plugin:PagerDutyPlugin',
            'pivotal = sentry_plugins.pivotal.plugin:PivotalPlugin',
            'pushover = sentry_plugins.pushover.plugin:PushoverPlugin',
            'segment = sentry_plugins.segment.plugin:SegmentPlugin',
            'slack = sentry_plugins.slack.plugin:SlackPlugin',
            'victorops = sentry_plugins.victorops.plugin:VictorOpsPlugin',
        ],
    },
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: Software Development'
    ],
)
