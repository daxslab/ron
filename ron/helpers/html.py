#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
| This file is part of the web2py Web Framework
| Copyrighted by Massimo Di Pierro <mdipierro@cs.depaul.edu>
| License: LGPLv3 (http://www.gnu.org/licenses/lgpl.html)

Template helpers
--------------------------------------------
"""
from __future__ import print_function

from functools import reduce
import pickle
import copyreg
from html.parser import HTMLParser
from html.entities import entitydefs, name2codepoint
import cgi
import os
import re
import base64
import itertools
from ron.gluon import sanitizer, decoder
from ron.gluon.utils import iteritems, local_html_escape, to_bytes, to_native, to_unicode, implements_bool, web2py_uuid
import marshal


regex_crlf = re.compile('\r|\n')

join = ''.join

# name2codepoint is incomplete respect to xhtml (and xml): 'apos' is missing.
entitydefs = dict(map(lambda k_v: (k_v[0], chr(k_v[1]).encode('utf-8')), iteritems(name2codepoint)))
entitydefs.setdefault('apos', u"'".encode('utf-8'))

__all__ = [
    'A',
    'B',
    'BODY',
    'BR',
    'BUTTON',
    'CENTER',
    'CAT',
    'COL',
    'COLGROUP',
    'DIV',
    'EM',
    'EMBED',
    'FIELDSET',
    'H1',
    'H2',
    'H3',
    'H4',
    'H5',
    'H6',
    'HEAD',
    'HR',
    'HTML',
    'I',
    'IFRAME',
    'IMG',
    'INPUT',
    'LABEL',
    'LEGEND',
    'LI',
    'LINK',
    'OL',
    'UL',
    'META',
    'OBJECT',
    'ON',
    'OPTION',
    'P',
    'PRE',
    'SCRIPT',
    'OPTGROUP',
    'SELECT',
    'SPAN',
    'STRONG',
    'STYLE',
    'TABLE',
    'TAG',
    'TD',
    'TEXTAREA',
    'TH',
    'THEAD',
    'TBODY',
    'TFOOT',
    'TITLE',
    'TR',
    'TT',
    'XHTML',
    'XML',
    'xmlescape',
    'embed64',
]

DEFAULT_PASSWORD_DISPLAY = '*' * 8


def xmlescape(data, quote=True):
    """
    Returns an escaped string of the provided data

    Args:
        data: the data to be escaped
        quote: optional (default False)
    """

    # first try the xml function
    if hasattr(data, 'xml') and callable(data.xml):
        return to_bytes(data.xml())

    if not (isinstance(data, (str, bytes))):
        # i.e., integers
        data = str(data)
    data = to_bytes(data, 'utf8', 'xmlcharrefreplace')

    # ... and do the escaping
    data = local_html_escape(data, quote)
    return data


def call_as_list(f, *a, **b):
    if not isinstance(f, (list, tuple)):
        f = [f]
    for item in f:
        item(*a, **b)


def truncate_string(text, length, dots='...'):
    text = to_unicode(text)
    if len(text) > length:
        text = to_native(text[:length - len(dots)]) + dots
    return text


ON = True


class XmlComponent(object):
    """
    Abstract root for all Html components
    """

    # TODO: move some DIV methods to here

    def xml(self):
        raise NotImplementedError

    def __mul__(self, n):
        return CAT(*[self for i in range(n)])

    def __add__(self, other):
        if isinstance(self, CAT):
            components = self.components
        else:
            components = [self]
        if isinstance(other, CAT):
            components += other.components
        else:
            components += [other]
        return CAT(*components)

    def add_class(self, name):
        """
        add a class to _class attribute
        """
        c = self['_class']
        classes = (set(c.split()) if c else set()) | set(name.split())
        self['_class'] = ' '.join(classes) if classes else None
        return self

    def remove_class(self, name):
        """
        remove a class from _class attribute
        """
        c = self['_class']
        classes = (set(c.split()) if c else set()) - set(name.split())
        self['_class'] = ' '.join(classes) if classes else None
        return self


class XML(XmlComponent):
    """
    use it to wrap a string that contains XML/HTML so that it will not be
    escaped by the template

    Examples:

    >>> XML('<h1>Hello</h1>').xml()
    '<h1>Hello</h1>'
    """

    def __init__(
            self,
            text,
            sanitize=False,
            permitted_tags=[
                'a',
                'b',
                'blockquote',
                'br/',
                'i',
                'li',
                'ol',
                'ul',
                'p',
                'cite',
                'code',
                'pre',
                'img/',
                'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                'table', 'tr', 'td', 'div',
                'strong', 'span',
            ],
            allowed_attributes={
                'a': ['href', 'title', 'target'],
                'img': ['src', 'alt'],
                'blockquote': ['type'],
                'td': ['colspan'],
            },
    ):
        """
        Args:
            text: the XML text
            sanitize: sanitize text using the permitted tags and allowed
                attributes (default False)
            permitted_tags: list of permitted tags (default: simple list of
                tags)
            allowed_attributes: dictionary of allowed attributed (default
                for A, IMG and BlockQuote).
                The key is the tag; the value is a list of allowed attributes.
        """
        if isinstance(text, str):
            text = to_native(text.encode('utf8', 'xmlcharrefreplace'))
        if sanitize:
            text = sanitizer.sanitize(text, permitted_tags, allowed_attributes)
        elif isinstance(text, bytes):
            text = to_native(text)
        elif not isinstance(text, str):
            text = str(text)
        self.text = text

    def xml(self):
        return to_bytes(self.text)

    def __str__(self):
        return self.text

    __repr__ = __str__

    def __add__(self, other):
        return '%s%s' % (self, other)

    def __radd__(self, other):
        return '%s%s' % (other, self)

    # def __cmp__(self, other):
    #     return cmp(str(self), str(other))

    def __hash__(self):
        return hash(str(self))

    #    why was this here? Break unpickling in sessions
    #    def __getattr__(self, name):
    #        return getattr(str(self), name)

    def __getitem__(self, i):
        return str(self)[i]

    def __getslice__(self, i, j):
        return str(self)[i:j]

    def __iter__(self):
        for c in str(self):
            yield c

    def __len__(self):
        return len(str(self))

    def flatten(self, render=None):
        """
        returns the text stored by the XML object rendered
        by the `render` function
        """
        if render:
            return render(self.text, None, {})
        return self.text

    def elements(self, *args, **kargs):
        """
        to be considered experimental since the behavior of this method
        is questionable
        another option could be `TAG(self.text).elements(*args, **kwargs)`
        """
        return []


# ## important to allow safe session.flash=T(....)


def XML_unpickle(data):
    return XML(marshal.loads(data))


def XML_pickle(data):
    return XML_unpickle, (marshal.dumps(str(data)),)


copyreg.pickle(XML, XML_pickle, XML_unpickle)


@implements_bool
class DIV(XmlComponent):
    """
    HTML helper, for easy generating and manipulating a DOM structure.
    Little or no validation is done.

    Behaves like a dictionary regarding updating of attributes.
    Behaves like a list regarding inserting/appending components.

    Examples:

    >>> DIV('hello', 'world', _style='color:red;').xml()
    '<div style=\"color:red;\">helloworld</div>'

    All other HTML helpers are derived from `DIV`.

    `_something="value"` attributes are transparently translated into
    `something="value"` HTML attributes
    """

    # name of the tag, subclasses should update this
    # tags ending with a '/' denote classes that cannot
    # contain components
    tag = 'div'

    def __init__(self, *components, **attributes):
        """
        Args:
            components: any components that should be nested in this element
            attributes: any attributes you want to give to this element

        Raises:
            SyntaxError: when a stand alone tag receives components
        """

        if self.tag[-1:] == '/' and components:
            raise SyntaxError('<%s> tags cannot have components'
                              % self.tag)
        if len(components) == 1 and isinstance(components[0], (list, tuple)):
            self.components = list(components[0])
        else:
            self.components = list(components)
        self.attributes = attributes
        self._fixup()
        # converts special attributes in components attributes
        self.parent = None
        for c in self.components:
            self._setnode(c)
        self._postprocessing()

    def update(self, **kargs):
        """
        dictionary like updating of the tag attributes
        """

        for (key, value) in iteritems(kargs):
            self[key] = value
        return self

    def append(self, value):
        """
        list style appending of components

        Examples:

        >>> a=DIV()
        >>> a.append(SPAN('x'))
        >>> print(a)
        <div><span>x</span></div>
        """
        self._setnode(value)
        ret = self.components.append(value)
        self._fixup()
        return ret

    def insert(self, i, value):
        """
        List-style inserting of components

        Examples:

        >>> a=DIV()
        >>> a.insert(0, SPAN('x'))
        >>> print(a)
        <div><span>x</span></div>
        """
        self._setnode(value)
        ret = self.components.insert(i, value)
        self._fixup()
        return ret

    def __getitem__(self, i):
        """
        Gets attribute with name 'i' or component #i.
        If attribute 'i' is not found returns None

        Args:
            i: index. If i is a string: the name of the attribute
                otherwise references to number of the component
        """

        if isinstance(i, str):
            try:
                return self.attributes[i]
            except KeyError:
                return None
        else:
            return self.components[i]

    def get(self, i):
        return self.attributes.get(i)

    def __setitem__(self, i, value):
        """
        Sets attribute with name 'i' or component #i.

        Args:
            i: index. If i is a string: the name of the attribute
                otherwise references to number of the component
            value: the new value
        """
        self._setnode(value)
        if isinstance(i, (str, str)):
            self.attributes[i] = value
        else:
            self.components[i] = value

    def __delitem__(self, i):
        """
        Deletes attribute with name 'i' or component #i.

        Args:
            i: index. If i is a string: the name of the attribute
                otherwise references to number of the component
        """

        if isinstance(i, str):
            del self.attributes[i]
        else:
            del self.components[i]

    def __len__(self):
        """
        Returns the number of included components
        """
        return len(self.components)

    def __bool__(self):
        """
        Always returns True
        """
        return True

    def _fixup(self):
        """
        Handling of provided components.

        Nothing to fixup yet. May be overridden by subclasses,
        eg for wrapping some components in another component or blocking them.
        """
        return

    def _wrap_components(self, allowed_parents,
                         wrap_parent=None,
                         wrap_lambda=None):
        """
        helper for _fixup. Checks if a component is in allowed_parents,
        otherwise wraps it in wrap_parent

        Args:
            allowed_parents: (tuple) classes that the component should be an
                instance of
            wrap_parent: the class to wrap the component in, if needed
            wrap_lambda: lambda to use for wrapping, if needed

        """
        components = []
        for c in self.components:
            if isinstance(c, (allowed_parents, CAT)):
                pass
            elif wrap_lambda:
                c = wrap_lambda(c)
            else:
                c = wrap_parent(c)
            if isinstance(c, DIV):
                c.parent = self
            components.append(c)
        self.components = components

    def _postprocessing(self):
        """
        Handling of attributes (normally the ones not prefixed with '_').

        Nothing to postprocess yet. May be overridden by subclasses
        """
        return

    def _traverse(self, status, hideerror=False):
        # TODO: docstring
        newstatus = status
        for c in self.components:
            if hasattr(c, '_traverse') and callable(c._traverse):
                c.vars = self.vars
                c.request_vars = self.request_vars
                c.errors = self.errors
                c.latest = self.latest
                c.session = self.session
                c.formname = self.formname
                if not c.attributes.get('hideerror'):
                    c['hideerror'] = hideerror or self.attributes.get('hideerror')
                newstatus = c._traverse(status, hideerror) and newstatus

        # for input, textarea, select, option
        # deal with 'value' and 'validation'

        name = self['_name']
        if newstatus:
            newstatus = self._validate()
            self._postprocessing()
        elif 'old_value' in self.attributes:
            self['value'] = self['old_value']
            self._postprocessing()
        elif name and name in self.vars:
            self['value'] = self.vars[name]
            self._postprocessing()
        if name:
            self.latest[name] = self['value']
        return newstatus

    def _validate(self):
        """
        nothing to validate yet. May be overridden by subclasses
        """
        return True

    def _setnode(self, value):
        if isinstance(value, DIV):
            value.parent = self

    def _xml(self):
        """
        Helper for xml generation. Returns separately:
        - the component attributes
        - the generated xml of the inner components

        Component attributes start with an underscore ('_') and
        do not have a False or None value. The underscore is removed.
        A value of True is replaced with the attribute name.

        Returns:
            tuple: (attributes, components)
        """

        # get the attributes for this component
        # (they start with '_', others may have special meanings)
        attr = []
        for key, value in iteritems(self.attributes):
            if key[:1] != '_':
                continue
            name = key[1:]
            if value is True:
                value = name
            elif value is False or value is None:
                continue
            attr.append((name, value))
        data = self.attributes.get('data', {})
        for key, value in iteritems(data):
            name = 'data-' + key
            value = data[key]
            attr.append((name, value))
        attr.sort()
        fa = b''
        for name, value in attr:
            fa += (b' %s="%s"') % (to_bytes(name), xmlescape(value, True))

        # get the xml for the inner components
        co = b''.join([xmlescape(component) for component in self.components])
        return (fa, co)

    def xml(self):
        """
        generates the xml for this component.
        """

        (fa, co) = self._xml()

        if not self.tag:
            return co

        tagname = to_bytes(self.tag)
        if tagname[-1:] == b'/':
            # <tag [attributes] />
            return b'<%s%s />' % (tagname[:-1], fa)

        # else: <tag [attributes]>  inner components xml </tag>
        xml_tag = b'<%s%s>%s</%s>' % (tagname, fa, co, tagname)
        return xml_tag

    def __str__(self):
        """
        str(COMPONENT) returns COMPONENT.xml()
        """
        # In PY3 __str__ cannot return bytes (TypeError: __str__ returned non-string (type bytes))
        return to_native(self.xml())

    def flatten(self, render=None):
        """
        Returns the text stored by the DIV object rendered by the render function
        the render function must take text, tagname, and attributes
        `render=None` is equivalent to `render=lambda text, tag, attr: text`

        Examples:

        >>> markdown = lambda text, tag=None, attributes={}: \
                        {None: re.sub('\s+',' ',text), \
                         'h1':'#'+text+'\\n\\n', \
                         'p':text+'\\n'}.get(tag,text)
        >>> a=TAG('<h1>Header</h1><p>this is a     test</p>')
        >>> a.flatten(markdown)
        '#Header\\n\\nthis is a test\\n'
        """

        text = ''
        for c in self.components:
            if isinstance(c, XmlComponent):
                s = c.flatten(render)
            elif render:
                s = render(to_native(c))
            else:
                s = to_native(c)
            text += s
        if render:
            text = render(text, self.tag, self.attributes)
        return text

    regex_tag = re.compile('^[\w\-\:]+')
    regex_id = re.compile('#([\w\-]+)')
    regex_class = re.compile('\.([\w\-]+)')
    regex_attr = re.compile('\[([\w\-\:]+)=(.*?)\]')

    def elements(self, *args, **kargs):
        """
        Find all components that match the supplied attribute dictionary,
        or None if nothing could be found

        All components of the components are searched.

        Examples:

        >>> a = DIV(DIV(SPAN('x'),3,DIV(SPAN('y'))))
        >>> for c in a.elements('span', first_only=True): c[0]='z'
        >>> print(a)
        <div><div><span>z</span>3<div><span>y</span></div></div></div>
        >>> for c in a.elements('span'): c[0]='z'
        >>> print(a)
        <div><div><span>z</span>3<div><span>z</span></div></div></div>

        It also supports a syntax compatible with jQuery

        Examples:

        >>> a=TAG('<div><span><a id="1-1" u:v=$>hello</a></span><p class="this is a test">world</p></div>')
        >>> for e in a.elements('div a#1-1, p.is'): print(e.flatten())
        hello
        world
        >>> for e in a.elements('#1-1'): print(e.flatten())
        hello
        >>> a.elements('a[u:v=$]')[0].xml()
        '<a id="1-1" u:v="$">hello</a>'
        >>> a=FORM( INPUT(_type='text'), SELECT(list(range(1))), TEXTAREA() )
        >>> for c in a.elements('input, select, textarea'): c['_disabled'] = 'disabled'
        >>> a.xml()
        '<form action="#" enctype="multipart/form-data" method="post"><input disabled="disabled" type="text" /><select disabled="disabled"><option value="0">0</option></select><textarea cols="40" disabled="disabled" rows="10"></textarea></form>'

        Elements that are matched can also be replaced or removed by specifying
        a "replace" argument (note, a list of the original matching elements
        is still returned as usual).

        Examples:

        >>> a = DIV(DIV(SPAN('x', _class='abc'), DIV(SPAN('y', _class='abc'), SPAN('z', _class='abc'))))
        >>> b = a.elements('span.abc', replace=P('x', _class='xyz'))
        >>> print(a)  # We should .xml() here instead of print
        <div><div><p class="xyz">x</p><div><p class="xyz">x</p><p class="xyz">x</p></div></div></div>

        "replace" can be a callable, which will be passed the original element and
        should return a new element to replace it.

        Examples:

        >>> a = DIV(DIV(SPAN('x', _class='abc'), DIV(SPAN('y', _class='abc'), SPAN('z', _class='abc'))))
        >>> b = a.elements('span.abc', replace=lambda el: P(el[0], _class='xyz'))
        >>> print(a)
        <div><div><p class="xyz">x</p><div><p class="xyz">y</p><p class="xyz">z</p></div></div></div>

        If replace=None, matching elements will be removed completely.

        Examples:

        >>> a = DIV(DIV(SPAN('x', _class='abc'), DIV(SPAN('y', _class='abc'), SPAN('z', _class='abc'))))
        >>> b = a.elements('span', find='y', replace=None)
        >>> print(a)
        <div><div><span class="abc">x</span><div><span class="abc">z</span></div></div></div>

        If a "find_text" argument is specified, elements will be searched for text
        components that match find_text, and any matching text components will be
        replaced (find_text is ignored if "replace" is not also specified).
        Like the "find" argument, "find_text" can be a string or a compiled regex.

        Examples:

        >>> a = DIV(DIV(SPAN('x', _class='abc'), DIV(SPAN('y', _class='abc'), SPAN('z', _class='abc'))))
        >>> b = a.elements(find_text=re.compile('x|y|z'), replace='hello')
        >>> print(a)
        <div><div><span class="abc">hello</span><div><span class="abc">hello</span><span class="abc">hello</span></div></div></div>

        If other attributes are specified aint with find_text, then only components
        that match the specified attributes will be searched for find_text.

        Examples:

        >>> a = DIV(DIV(SPAN('x', _class='abc'), DIV(SPAN('y', _class='efg'), SPAN('z', _class='abc'))))
        >>> b = a.elements('span.efg', find_text=re.compile('x|y|z'), replace='hello')
        >>> print(a)
        <div><div><span class="abc">x</span><div><span class="efg">hello</span><span class="abc">z</span></div></div></div>
        """
        if len(args) == 1:
            args = [a.strip() for a in args[0].split(',')]
        if len(args) > 1:
            subset = [self.elements(a, **kargs) for a in args]
            return reduce(lambda a, b: a + b, subset, [])
        elif len(args) == 1:
            items = args[0].split()
            if len(items) > 1:
                subset = [a.elements(' '.join(
                    items[1:]), **kargs) for a in self.elements(items[0])]
                return reduce(lambda a, b: a + b, subset, [])
            else:
                item = items[0]
                if '#' in item or '.' in item or '[' in item:
                    match_tag = self.regex_tag.search(item)
                    match_id = self.regex_id.search(item)
                    match_class = self.regex_class.search(item)
                    match_attr = self.regex_attr.finditer(item)
                    args = []
                    if match_tag:
                        args = [match_tag.group()]
                    if match_id:
                        kargs['_id'] = match_id.group(1)
                    if match_class:
                        kargs['_class'] = re.compile('(?<!\w)%s(?!\w)' %
                                                     match_class.group(1).replace('-', '\\-').replace(':', '\\:'))
                    for item in match_attr:
                        kargs['_' + item.group(1)] = item.group(2)
                    return self.elements(*args, **kargs)
        # make a copy of the components
        matches = []
        # check if the component has an attribute with the same
        # value as provided
        tag = to_native(getattr(self, 'tag')).replace('/', '')
        check = not (args and tag not in args)
        for (key, value) in iteritems(kargs):
            if key not in ['first_only', 'replace', 'find_text']:
                if isinstance(value, (str, int)):
                    if str(self[key]) != str(value):
                        check = False
                elif key in self.attributes:
                    if not value.search(str(self[key])):
                        check = False
                else:
                    check = False
        if 'find' in kargs:
            find = kargs['find']
            is_regex = not isinstance(find, (str, int))
            for c in self.components:
                if (isinstance(c, str) and ((is_regex and find.search(c)) or
                                            (str(find) in c))):
                    check = True
        # if found, return the component
        if check:
            matches.append(self)

        first_only = kargs.get('first_only', False)
        replace = kargs.get('replace', False)
        find_text = replace is not False and kargs.get('find_text', False)
        is_regex = not isinstance(find_text, (str, int, bool))
        find_components = not (check and first_only)

        def replace_component(i):
            if replace is None:
                del self[i]
                return i
            else:
                self[i] = replace(self[i]) if callable(replace) else replace
                return i + 1

        # loop the components
        if find_text or find_components:
            i = 0
            while i < len(self.components):
                c = self[i]
                j = i + 1
                if check and find_text and isinstance(c, str) and \
                        ((is_regex and find_text.search(c)) or (str(find_text) in c)):
                    j = replace_component(i)
                elif find_components and isinstance(c, XmlComponent):
                    child_matches = c.elements(*args, **kargs)
                    if len(child_matches):
                        if not find_text and replace is not False and child_matches[0] is c:
                            j = replace_component(i)
                        if first_only:
                            return child_matches
                        matches.extend(child_matches)
                i = j
        return matches

    def element(self, *args, **kargs):
        """
        Finds the first component that matches the supplied attribute dictionary,
        or None if nothing could be found

        Also the components of the components are searched.
        """
        kargs['first_only'] = True
        elements = self.elements(*args, **kargs)
        if not elements:
            # we found nothing
            return None
        return elements[0]

    def siblings(self, *args, **kargs):
        """
        Finds all sibling components that match the supplied argument list
        and attribute dictionary, or None if nothing could be found
        """
        sibs = [s for s in self.parent.components if not s == self]
        matches = []
        first_only = False
        if 'first_only' in kargs:
            first_only = kargs.pop('first_only')
        for c in sibs:
            try:
                check = True
                tag = getattr(c, 'tag').replace("/", "")
                if args and tag not in args:
                    check = False
                for (key, value) in iteritems(kargs):
                    if c[key] != value:
                        check = False
                if check:
                    matches.append(c)
                    if first_only:
                        break
            except:
                pass
        return matches

    def sibling(self, *args, **kargs):
        """
        Finds the first sibling component that match the supplied argument list
        and attribute dictionary, or None if nothing could be found
        """
        kargs['first_only'] = True
        sibs = self.siblings(*args, **kargs)
        if not sibs:
            return None
        return sibs[0]


class CAT(DIV):
    tag = ''


def TAG_unpickler(data):
    return pickle.loads(data)


def TAG_pickler(data):
    d = DIV()
    d.__dict__ = data.__dict__
    marshal_dump = pickle.dumps(d, pickle.HIGHEST_PROTOCOL)
    return (TAG_unpickler, (marshal_dump,))


class __tag_div__(DIV):
    def __init__(self, name, *a, **b):
        DIV.__init__(self, *a, **b)
        self.tag = name


copyreg.pickle(__tag_div__, TAG_pickler, TAG_unpickler)


class __TAG__(XmlComponent):
    """
    TAG factory

    Examples:

    >>> print(TAG.first(TAG.second('test'), _key = 3))
    <first key=\"3\"><second>test</second></first>

    """

    def __getitem__(self, name):
        return self.__getattr__(name)

    def __getattr__(self, name):
        if name[-1:] == '_':
            name = name[:-1] + '/'
        return lambda *a, **b: __tag_div__(name, *a, **b)

    def __call__(self, html):
        return web2pyHTMLParser(decoder.decoder(html)).tree


TAG = __TAG__()


class HTML(DIV):
    """
    There are four predefined document type definitions.
    They can be specified in the 'doctype' parameter:

    - 'strict' enables strict doctype
    - 'transitional' enables transitional doctype (default)
    - 'frameset' enables frameset doctype
    - 'html5' enables HTML 5 doctype
    - any other string will be treated as user's own doctype

    'lang' parameter specifies the language of the document.
    Defaults to 'en'.

    See also `DIV`
    """

    tag = b'html'

    strict = b'<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">\n'
    transitional = \
        b'<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">\n'
    frameset = \
        b'<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Frameset//EN" "http://www.w3.org/TR/html4/frameset.dtd">\n'
    html5 = b'<!DOCTYPE HTML>\n'

    def xml(self):
        lang = self['lang']
        if not lang:
            lang = 'en'
        self.attributes['_lang'] = lang
        doctype = self['doctype']
        if doctype is None:
            doctype = self.transitional
        elif doctype == 'strict':
            doctype = self.strict
        elif doctype == 'transitional':
            doctype = self.transitional
        elif doctype == 'frameset':
            doctype = self.frameset
        elif doctype == 'html5':
            doctype = self.html5
        elif doctype == '':
            doctype = b''
        else:
            doctype = b'%s\n' % to_bytes(doctype)
        (fa, co) = self._xml()

        return b'%s<%s%s>%s</%s>' % (doctype, self.tag, fa, co, self.tag)


class XHTML(DIV):
    """
    This is XHTML version of the HTML helper.

    There are three predefined document type definitions.
    They can be specified in the 'doctype' parameter:

    - 'strict' enables strict doctype
    - 'transitional' enables transitional doctype (default)
    - 'frameset' enables frameset doctype
    - any other string will be treated as user's own doctype

    'lang' parameter specifies the language of the document and the xml document.
    Defaults to 'en'.

    'xmlns' parameter specifies the xml namespace.
    Defaults to 'http://www.w3.org/1999/xhtml'.

    See also `DIV`
    """

    tag = b'html'

    strict = b'<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n'
    transitional = b'<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n'
    frameset = b'<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Frameset//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-frameset.dtd">\n'
    xmlns = 'http://www.w3.org/1999/xhtml'

    def xml(self):
        xmlns = self['xmlns']
        if xmlns:
            self.attributes['_xmlns'] = xmlns
        else:
            self.attributes['_xmlns'] = self.xmlns
        lang = self['lang']
        if not lang:
            lang = 'en'
        self.attributes['_lang'] = lang
        self.attributes['_xml:lang'] = lang
        doctype = self['doctype']
        if doctype:
            if doctype == 'strict':
                doctype = self.strict
            elif doctype == 'transitional':
                doctype = self.transitional
            elif doctype == 'frameset':
                doctype = self.frameset
            else:
                doctype = b'%s\n' % to_bytes(doctype)
        else:
            doctype = self.transitional
        (fa, co) = self._xml()
        return b'%s<%s%s>%s</%s>' % (doctype, self.tag, fa, co, self.tag)


class HEAD(DIV):
    tag = 'head'


class TITLE(DIV):
    tag = 'title'


class META(DIV):
    tag = 'meta/'


class LINK(DIV):
    tag = 'link/'


class SCRIPT(DIV):
    tag = b'script'
    tagname = to_bytes(tag)

    def xml(self):
        (fa, co) = self._xml()
        fa = to_bytes(fa)
        # no escaping of subcomponents
        co = b'\n'.join([to_bytes(component) for component in
                         self.components])
        if co:
            # <script [attributes]><!--//--><![CDATA[//><!--
            # script body
            # //--><!]]></script>
            # return '<%s%s><!--//--><![CDATA[//><!--\n%s\n//--><!]]></%s>' % (self.tag, fa, co, self.tag)
            return b'<%s%s><!--\n%s\n//--></%s>' % (self.tagname, fa, co, self.tagname)
        else:
            return DIV.xml(self)


class STYLE(DIV):
    tag = 'style'
    tagname = to_bytes(tag)

    def xml(self):
        (fa, co) = self._xml()
        fa = to_bytes(fa)
        # no escaping of subcomponents
        co = b'\n'.join([to_bytes(component) for component in
                         self.components])
        if co:
            # <style [attributes]><!--/*--><![CDATA[/*><!--*/
            # style body
            # /*]]>*/--></style>
            return b'<%s%s><!--/*--><![CDATA[/*><!--*/\n%s\n/*]]>*/--></%s>' % (self.tagname, fa, co, self.tagname)
        else:
            return DIV.xml(self)


class IMG(DIV):
    tag = 'img/'


class SPAN(DIV):
    tag = 'span'


class BODY(DIV):
    tag = 'body'


class H1(DIV):
    tag = 'h1'


class H2(DIV):
    tag = 'h2'


class H3(DIV):
    tag = 'h3'


class H4(DIV):
    tag = 'h4'


class H5(DIV):
    tag = 'h5'


class H6(DIV):
    tag = 'h6'


class P(DIV):
    """
    Will replace ``\\n`` by ``<br />`` if the `cr2br` attribute is provided.

    see also `DIV`
    """

    tag = 'p'

    def xml(self):
        text = DIV.xml(self)
        if self['cr2br']:
            text = text.replace(b'\n', b'<br />')
        return text


class STRONG(DIV):
    tag = 'strong'


class B(DIV):
    tag = 'b'


class BR(DIV):
    tag = 'br/'


class HR(DIV):
    tag = 'hr/'


class A(DIV):
    """
    Generates an A() link.
    A() in web2py is really important and with the included web2py.js
    allows lots of Ajax interactions in the page

    On top of "usual" `_attributes`, it takes

    Args:
        callback: an url to call but not redirect to
        cid: if you want to load the _href into an element of the page (component)
            pass its id (without the #) here
        delete: element to delete after calling callback
        target: same thing as cid
        confirm: text to display upon a callback with a delete
        noconfirm: don't display alert upon a callback with delete

    """

    tag = 'a'

    def xml(self):
        if not self.components and self['_href']:
            self.append(self['_href'])
        disable_needed = ['callback', 'cid', 'delete', 'component', 'target']
        disable_needed = any((self[attr] for attr in disable_needed))
        if disable_needed:
            self['_data-w2p_disable_with'] = self['_disable_with'] or 'default'
            self['_disable_with'] = None
        if self['callback'] and not self['_id']:
            self['_id'] = web2py_uuid()
        if self['delete']:
            self['_data-w2p_remove'] = self['delete']
        if self['target']:
            if self['target'] == '<self>':
                self['target'] = self['_id']
            self['_data-w2p_target'] = self['target']
        if self['component']:
            self['_data-w2p_method'] = 'GET'
            self['_href'] = self['component']
        elif self['callback']:
            self['_data-w2p_method'] = 'POST'
            self['_href'] = self['callback']
            if self['delete'] and not self['noconfirm']:
                if not self['confirm']:
                    self['_data-w2p_confirm'] = 'default'
                else:
                    self['_data-w2p_confirm'] = self['confirm']
        elif self['cid']:
            self['_data-w2p_method'] = 'GET'
            self['_data-w2p_target'] = self['cid']
            if self['pre_call']:
                self['_data-w2p_pre_call'] = self['pre_call']
        return DIV.xml(self)


class BUTTON(DIV):
    tag = 'button'


class EM(DIV):
    tag = 'em'


class EMBED(DIV):
    tag = 'embed/'


class TT(DIV):
    tag = 'tt'


class PRE(DIV):
    tag = 'pre'


class CENTER(DIV):
    tag = 'center'


class LABEL(DIV):
    tag = 'label'


class LI(DIV):
    tag = 'li'


class UL(DIV):
    """
    UL Component.

    If subcomponents are not LI-components they will be wrapped in a LI

    """

    tag = 'ul'

    def _fixup(self):
        self._wrap_components(LI, LI)


class OL(UL):
    tag = 'ol'


class TD(DIV):
    tag = 'td'


class TH(DIV):
    tag = 'th'


class TR(DIV):
    """
    TR Component.

    If subcomponents are not TD/TH-components they will be wrapped in a TD

    """

    tag = 'tr'

    def _fixup(self):
        self._wrap_components((TD, TH), TD)


class __TRHEAD__(DIV):
    """
    __TRHEAD__ Component, internal only

    If subcomponents are not TD/TH-components they will be wrapped in a TH

    """

    tag = 'tr'

    def _fixup(self):
        self._wrap_components((TD, TH), TH)


class THEAD(DIV):
    tag = 'thead'

    def _fixup(self):
        self._wrap_components((__TRHEAD__, TR), __TRHEAD__)


class TBODY(DIV):
    tag = 'tbody'

    def _fixup(self):
        self._wrap_components(TR, TR)


class TFOOT(DIV):
    tag = 'tfoot'

    def _fixup(self):
        self._wrap_components(TR, TR)


class COL(DIV):
    tag = 'col/'


class COLGROUP(DIV):
    tag = 'colgroup'


class TABLE(DIV):
    """
    TABLE Component.

    If subcomponents are not TR/TBODY/THEAD/TFOOT-components
    they will be wrapped in a TR

    """

    tag = 'table'

    def _fixup(self):
        self._wrap_components((TR, TBODY, THEAD, TFOOT, COL, COLGROUP), TR)


class I(DIV):
    tag = 'i'


class IFRAME(DIV):
    tag = 'iframe'


class INPUT(DIV):
    """
    INPUT Component

    Takes two special attributes value= and requires=.

    Args:
        value: used to pass the initial value for the input field.
            value differs from _value because it works for checkboxes, radio,
            textarea and select/option too.
            For a checkbox value should be '' or 'on'.
            For a radio or select/option value should be the _value
            of the checked/selected item.

        requires: should be None, or a validator or a list of validators
            for the value of the field.

    Examples:

    >>> INPUT(_type='text', _name='name', value='Max').xml()
    '<input name=\"name\" type=\"text\" value=\"Max\" />'

    >>> INPUT(_type='checkbox', _name='checkbox', value='on').xml()
    '<input checked=\"checked\" name=\"checkbox\" type=\"checkbox\" value=\"on\" />'

    >>> INPUT(_type='radio', _name='radio', _value='yes', value='yes').xml()
    '<input checked=\"checked\" name=\"radio\" type=\"radio\" value=\"yes\" />'

    >>> INPUT(_type='radio', _name='radio', _value='no', value='yes').xml()
    '<input name=\"radio\" type=\"radio\" value=\"no\" />'


        """

    tag = 'input/'

    def _validate(self):

        # # this only changes value, not _value

        name = self['_name']
        if name is None or name == '':
            return True
        name = str(name)
        request_vars_get = self.request_vars.get
        if self['_type'] != 'checkbox':
            self['old_value'] = self['value'] or self['_value'] or ''
            value = request_vars_get(name, '')
            self['value'] = value if not hasattr(value, 'file') else None
        else:
            self['old_value'] = self['value'] or False
            value = request_vars_get(name)
            if isinstance(value, (tuple, list)):
                self['value'] = self['_value'] in value
            else:
                self['value'] = self['_value'] == value
        requires = self['requires']
        if requires:
            if not isinstance(requires, (list, tuple)):
                requires = [requires]
            for k, validator in enumerate(requires):
                try:
                    (value, errors) = validator(value)
                except:
                    import traceback
                    print(traceback.format_exc())
                    msg = "Validation error, field:%s %s" % (name, validator)
                    raise Exception(msg)
                if errors is not None:
                    self.vars[name] = value
                    self.errors[name] = errors
                    break
        if name not in self.errors:
            self.vars[name] = value
            return True
        return False

    def _postprocessing(self):
        t = self['_type']
        if not t:
            t = self['_type'] = 'text'
        t = t.lower()
        value = self['value']
        if self['_value'] is None or isinstance(self['_value'], cgi.FieldStorage):
            _value = None
        else:
            _value = str(self['_value'])
        if '_checked' in self.attributes and 'value' not in self.attributes:
            pass
        elif t == 'checkbox':
            if not _value:
                _value = self['_value'] = 'on'
            if not value:
                value = []
            elif value is True:
                value = [_value]
            elif not isinstance(value, (list, tuple)):
                value = str(value).split('|')
            self['_checked'] = _value in value and 'checked' or None
        elif t == 'radio':
            if str(value) == str(_value):
                self['_checked'] = 'checked'
            else:
                self['_checked'] = None
        elif t == 'password' and value != DEFAULT_PASSWORD_DISPLAY:
            self['value'] = ''
        elif not t == 'submit':
            if value is None:
                self['value'] = _value
            elif not isinstance(value, list):
                self['_value'] = value

    def xml(self):
        name = self.attributes.get('_name', None)
        if name and hasattr(self, 'errors') \
                and self.errors.get(name, None) \
                and self['hideerror'] is not True:
            self['_class'] = (self['_class'] and self['_class'] + ' ' or '') + 'invalidinput'
            return DIV.xml(self) + DIV(
                DIV(
                    self.errors[name], _class='error',
                    errors=None, _id='%s__error' % name),
                _class='error_wrapper').xml()
        else:
            if self['_class'] and self['_class'].endswith('invalidinput'):
                self['_class'] = self['_class'][:-12]
                if self['_class'] == '':
                    self['_class'] = None
            return DIV.xml(self)


class TEXTAREA(INPUT):
    """
    Examples::

        TEXTAREA(_name='sometext', value='blah ' * 100, requires=IS_NOT_EMPTY())

    'blah blah blah ...' will be the content of the textarea field.

    """

    tag = 'textarea'

    def _postprocessing(self):
        if '_rows' not in self.attributes:
            self['_rows'] = 10
        if '_cols' not in self.attributes:
            self['_cols'] = 40
        if self['value'] is not None:
            self.components = [self['value']]
        elif self.components:
            self['value'] = self.components[0]


class OPTION(DIV):
    tag = 'option'

    def _fixup(self):
        if '_value' not in self.attributes:
            self.attributes['_value'] = str(self.components[0])


class OBJECT(DIV):
    tag = 'object'


class OPTGROUP(DIV):
    tag = 'optgroup'

    def _fixup(self):
        components = []
        for c in self.components:
            if isinstance(c, OPTION):
                components.append(c)
            else:
                components.append(OPTION(c, _value=str(c)))
        self.components = components


class SELECT(INPUT):
    tag = 'select'

    def _fixup(self):
        components = []
        for c in self.components:
            if isinstance(c, (OPTION, OPTGROUP)):
                components.append(c)
            else:
                components.append(OPTION(c, _value=str(c)))
        self.components = components

    def _postprocessing(self):
        component_list = []
        for c in self.components:
            if isinstance(c, OPTGROUP):
                component_list.append(c.components)
            else:
                component_list.append([c])
        options = itertools.chain(*component_list)

        value = self['value']
        if value is not None:
            if not self['_multiple']:
                for c in options:  # my patch
                    if (value is not None) and (str(c['_value']) == str(value)):
                        c['_selected'] = 'selected'
                    else:
                        c['_selected'] = None
            else:
                if isinstance(value, (list, tuple)):
                    values = [str(item) for item in value]
                else:
                    values = [str(value)]
                for c in options:  # my patch
                    if (value is not None) and (str(c['_value']) in values):
                        c['_selected'] = 'selected'
                    else:
                        c['_selected'] = None


class FIELDSET(DIV):
    tag = 'fieldset'


class LEGEND(DIV):
    tag = 'legend'


def embed64(filename=None,
            file=None,
            data=None,
            extension='image/gif'
            ):
    """
    helper to encode the provided (binary) data into base64.

    Args:
        filename: if provided, opens and reads this file in 'rb' mode
        file: if provided, reads this file
        data: if provided, uses the provided data
    """

    if filename and os.path.exists(file):
        fp = open(filename, 'rb')
        data = fp.read()
        fp.close()
    data = base64.b64encode(data)
    return 'data:%s;base64,%s' % (extension, data)


class web2pyHTMLParser(HTMLParser):
    """
    obj = web2pyHTMLParser(text) parses and html/xml text into web2py helpers.
    obj.tree contains the root of the tree, and tree can be manipulated
    """

    def __init__(self, text, closed=('input', 'link')):
        HTMLParser.__init__(self)
        self.tree = self.parent = TAG['']()
        self.closed = closed
        self.last = None
        self.feed(text)

    def handle_starttag(self, tagname, attrs):
        if tagname in self.closed:
            tagname += '/'
        tag = TAG[tagname]()
        for key, value in attrs:
            tag['_' + key] = value
        tag.parent = self.parent
        self.parent.append(tag)
        if not tag.tag.endswith('/'):
            self.parent = tag
        else:
            self.last = tag.tag[:-1]

    def handle_data(self, data):
        if not isinstance(data, str):
            try:
                data = data.decode('utf8')
            except:
                data = data.decode('latin1')
        self.parent.append(data.encode('utf8', 'xmlcharref'))

    def handle_charref(self, name):
        if name.startswith('x'):
            self.parent.append(chr(int(name[1:], 16)).encode('utf8'))
        else:
            self.parent.append(chr(int(name)).encode('utf8'))

    def handle_entityref(self, name):
        self.parent.append(entitydefs[name])

    def handle_endtag(self, tagname):
        # this deals with unbalanced tags
        if tagname == self.last:
            return
        while True:
            try:
                parent_tagname = self.parent.tag
                self.parent = self.parent.parent
            except:
                raise RuntimeError("unable to balance tag %s" % tagname)
            if parent_tagname[:len(tagname)] == tagname:
                break
