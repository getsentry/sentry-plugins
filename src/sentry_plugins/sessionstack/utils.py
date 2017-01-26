from base64 import b64encode


def get_basic_auth(username, password):
    basic_auth = b64encode(username + ':' + password).decode('ascii')

    return 'Basic %s' % basic_auth


def remove_trailing_slashes(url):
    return url.strip().rstrip('/')
