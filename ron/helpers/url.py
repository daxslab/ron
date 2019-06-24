import urllib

from ron import request

def URL(*parts, vars=None, hash=None, scheme=False):
    """
    Helper who generates an URL
    Examples:
    URL('a','b',vars=dict(x=1),hash='y')       -> /{app_name}/a/b?x=1#y
    URL('a','b',vars=dict(x=1),scheme=None)    -> //{domain}/{app_name}/a/b?x=1
    URL('a','b',vars=dict(x=1),scheme=True)    -> http://{domain}/{app_name}/a/b?x=1
    URL('a','b',vars=dict(x=1),scheme='https') -> https://{domain}/{app_name}/a/b?x=1
    """
    prefix = '/'
    url = prefix + '/'.join(parts)
    if vars:
        url += '?' + '&'.join('%s=%s' % (k, urllib.parse.quote(str(v))) for k,v in vars.items())
    if hash:
        url += '#%s' % hash
    if not scheme is False:
        orig_scheme, _, domain = request.url.split('/')[:3]
        scheme = orig_scheme if scheme is True else '' if scheme is None else scheme + ':'
        url = '%s//%s%s' % (scheme, domain, url)
    return url
