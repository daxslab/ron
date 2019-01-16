import sys
import hashlib
import os


_identity = lambda x: x


import pickle
from io import StringIO, BytesIO

from importlib import reload


from http import cookies as Cookie
from urllib import parse as urlparse
from urllib import request as urllib2

import builtins as builtin
import _thread as thread
import configparser
import queue as Queue
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders as Encoders
from email.header import Header
from email.charset import Charset, add_charset, QP as charset_QP
from urllib.request import FancyURLopener, urlopen

from http import cookiejar as cookielib
from xmlrpc.client import ProtocolError
import html # warning, this is the python3 module and not the web2py html module
import ipaddress


implements_iterator = _identity
implements_bool = _identity





# shortcuts
pjoin = os.path.join
exists = os.path.exists
