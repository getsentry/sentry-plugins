Contributing
============

Refer to https://docs.sentry.io/internal/contributing/ for overall Sentry project
contributing guidelines.

In order to contribute to this repository, here's a few things you ought to know:

There's a root `Makefile` that contains most of the commands you are likely to need.

Some getting-started steps:

.. code-block:: shell

    git clone https://github.com/getsentry/sentry-plugins.git
    cd sentry-plugins
    # install Node dependencies, Python dependencies, Chrome Driver
    make install-tests

**macOS only note:** Currently, the Makefile assumes Linux OS, so the chromedriver installed to
``~/.bin/chromedriver`` won't work. Remove it, and run ``brew install chromedriver`` instead.

In order to execute the test suite, you will need a running redis server on ``localhost:6379``.

Local Sentry + Plugins
----------------------

If you want to run a local development version of sentry, that includes your plugin changes, a few
more items are needed.

- a running version of postgresql
- create a database for sentry::

    createdb sentry

- set up & start sentry::

    sentry init --dev # set pg username in ~/.sentry/sentry.conf.py
    sentry upgrade # performs all the db migrations, answer prompts for creating a new user
    sentry devserver

Once started, visit http://localhost:8000/ and log in with the user you created.
