sentry-plugins
==============

Extensions for Sentry. Includes Slack, GitHub, and HipChat.

Install the package via ``pip``::

    pip install sentry-plugins

Run migrations after installation is complete

    sentry upgrade

Asana
-----
You'll have to create an application in Asana to get a client ID and secret. Use the following for the redirect URL::

    <URL_TO_SENTRY>/account/settings/social/associate/complete/asana/

Ensure you've configured Asana auth in Sentry::

    ASANA_CLIENT_ID = 'Asana Client ID'
    ASANA_CLIENT_SECRET = 'Asana Client Secret'

GitHub
------

You'll have to create an application in GitHub to get the app ID and API secret. Use the following for the Authentication redirect URL::

    <URL_TO_SENTRY>/account/settings/social/associate/complete/github/

Ensure you've configured GitHub auth in Sentry::

    GITHUB_APP_ID = 'GitHub Application Client ID'
    GITHUB_API_SECRET = 'GitHub Application Client Secret'
    GITHUB_EXTENDED_PERMISSIONS = ['repo']

If the callback URL you've registered with GitHub uses HTTPS, you'll need this in your config::

    SOCIAL_AUTH_REDIRECT_IS_HTTPS = True

If your server is behind a reverse proxy, you'll need to enable the X-Forwarded-Proto
and X-Forwarded-Host headers, and use this config::

    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST = True


Associate your account with GitHub (if you haven't already) via Account -> Identities. If you had
already associated your account, and you hadn't configured extended permissions, you'll need to
disconnect and reconnect the account.

You'll now see a new action on groups which allows quick creation of GitHub issues.


Caveats
~~~~~~~

If you have multiple GitHub identities associated in Sentry, the plugin will just select
one to use.

GitLab
------

Go to your project's configuration page (Projects -> [Project] -> Issue Tracking) and select
GitLab. Enter the required credentials (use a `personal access
token<https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html>`_)
and click save changes.

It's recommended to create a specific user for Sentry with only `Reporter` privileges on your projects.


HipChat
-------

Go to your project's configuration page (Projects -> [Project]) and select the
Hipchat tab. Enter the required credentials and click save changes.


Slack
-------

Go to your project's configuration page (Projects -> [Project]) and select the
Slack tab. Enter the required credentials and click save changes.


Visual Studio (Team Services)
-----------------------------

You'll have to `create an application in Visual Studio <https://app.vsaex.visualstudio.com/app/register>`_ to get a client ID and secret.

**Redirect URL:**

::

    <URL_TO_SENTRY>/account/settings/social/associate/complete/visualstudio/


**Scopes:**

- Code (read) -- ``vso.code``
- Work items (read and write) -- ``vso.work_write``
- Project and Team (read) -- ``vso.project``
- Releases (read) -- ``vso.release``

Add the configured application credentials to your Sentry config:

.. code-block:: python

    VISUALSTUDIO_APP_ID = 'App ID'
    VISUALSTUDIO_APP_SECRET = 'App Secret'
    VISUALSTUDIO_CLIENT_SECRET = 'Client Secret'
    VISUALSTUDIO_SCOPES = ['vso.project', 'vso.work_write', 'vso.code', 'vso.release']

Development
~~~~~~~~~~~

Create a tunnel to localhost using something like https://ngrok.com/download::

    ngrok http 8000

Start Sentry with the following parameters set::

    AC_BASE_URL=https://<xxx>.ngrok.io HTTPS=on sentry devserver


JIRA (Atlassian Connect UI Plugin)
----------------------------------

Enable the plugin by adding it in the Add-on Management page in JIRA.

Development
~~~~~~~~~~~

Use https://ngrok.com to expose your local Sentry to the internet. Update your config.yml to use your ngrok url::

    system.url-prefix: 'https://<xxx>.ngrok.io'

From the manage add-on page in JIRA, choose 'Upload add-on' and copy the URL for the descriptor view.
