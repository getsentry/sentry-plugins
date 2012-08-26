sentry-github
=============

An extension for Sentry which integrates with GitHUb. Specifically, it allows you to easily create
issues from events within Sentry.


Install
-------

Install the package via ``pip``::

    pip install sentry-github

Ensure you've configured GitHub auth in Sentry::

    # https://github.com/settings/applications/new
    GITHUB_APP_ID = ''
    GITHUB_API_SECRET = '

Associate your account with GitHub (if you haven't already) via Account -> Identities.

.. note:: If you have multiple GitHub identities associated in Sentry, the plugin will just select
          one to use.

You'll now see a new action on groups which allows quick creation of GitHub issues.
