from __future__ import absolute_import


def get_secret_field_config(secret, help_text, include_prefix=False):
    has_saved_value = bool(secret)
    saved_text = 'Only enter a new value if you wish to update the existing one. '
    return {
        'type': 'secret',
        'has_saved_value': has_saved_value,
        'prefix': (secret or '')[:4] if include_prefix else '',
        'required': not has_saved_value,
        'help': '%s%s' % ((saved_text if has_saved_value else ''), help_text)
    }
