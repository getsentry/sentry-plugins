from __future__ import absolute_import

# Run tests against sqlite for simplicity
import os
os.environ.setdefault('DB', 'sqlite')

pytest_plugins = ['sentry.utils.pytest']
