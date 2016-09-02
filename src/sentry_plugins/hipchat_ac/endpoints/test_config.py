from __future__ import absolute_import

from sentry.plugins.endpoints import PluginProjectEndpoint


class HipchatTestConfigEndpoint(PluginProjectEndpoint):
    def post(self, request, project, *args, **kwargs):
        try:
            test_results = self.plugin.test_configuration(project)
        except Exception as exc:
            error = True
            if hasattr(exc, 'read') and callable(exc.read):
                test_results = '%s\n%s' % (exc, exc.read())
            else:
                test_results = 'There was an internal error with the Plugin.'
        else:
            error = False
            test_results = 'No errors returned'

        return self.respond({
            'message': test_results,
            'error': error,
        })
