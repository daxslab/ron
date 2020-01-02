import urllib

from ron import request

def URL(*parts, vars=None, hash=None, scheme=False, host=False):
    """
    Helper who generates an URL
    Examples:
    URL('a','b',vars=dict(x=1),hash='y')       -> /a/b?x=1#y
    URL('a','b',vars=dict(x=1),scheme=None)    -> //{domain}/a/b?x=1
    URL('a','b',vars=dict(x=1),scheme=True)    -> http://{domain}/a/b?x=1
    URL('a','b',vars=dict(x=1),scheme='https') -> https://{domain}/a/b?x=1
    """
    prefix = '/'
    url = prefix + '/'.join(parts)
    if vars:
        url += '?' + '&'.join('%s=%s' % (k, urllib.parse.quote(str(v))) for k,v in vars.items())
    if hash:
        url += '#%s' % hash

    orig_scheme, _, org_host = request.url.split('/')[:3]
    if scheme or host:
        if host:
            host = org_host if host is True else host
        else:
            host = org_host

        if scheme:
            scheme = orig_scheme if scheme is True else '' if scheme is None else scheme + ':'
        else:
            scheme = orig_scheme
        url = '%s//%s%s' % (scheme, host, url)
    return url
