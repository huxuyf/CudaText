import sys
import os
import re
import json
from cuda_fmt import get_config_filename

sys.path.append(os.path.dirname(__file__))
from . import sqlparse

def opt():
    fn = get_config_filename('SQL Parse')
    if os.path.isfile(fn):
        s = open(fn, 'r').read()
        #del // comments
        s = re.sub(r'(^|[^:])//.*', r'\1', s)
        d = json.loads(s)
    else:
        d = {}
    return d

def do_format(text):
    return sqlparse.format(text, **opt() )
