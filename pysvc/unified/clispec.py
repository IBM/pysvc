##############################################################################
# Copyright 2019 IBM Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
##############################################################################
'''Parsers for storage array's CLI specification XML'''

import base64
import re
import zlib
from pysvc.unified.helpers import xml_util as etree
from pysvc.unified.helpers.xml_util import XMLException
from logging import getLogger
import pysvc.errors as ce
import time
from pysvc.unified.response import find_response_helper, is_svc_response
from pysvc.unified.response import CLIFailureError
from collections import OrderedDict
from pysvc import PYSVC_DEFAULT_LOGGER

__all__ = ['parse']

xlog = getLogger(PYSVC_DEFAULT_LOGGER)

PATTERN_INVALID_CHAR = re.compile('[^a-zA-Z0-9_]')
TAG_ERR = 'error411049e268734c0c996d65b3854f1113'
KEY_STR = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
RETRY_TIME = 3
METADATA_RC_BUSY = 11


class CLISpecError(ce.StorageArrayClientException):
    '''Raise if CLI specification has error.'''
    pass


class CLIBase(object):
    def __init__(self):
        self.cmds = {}

    def add_cmd(self, realname, description='', resp_helper=None):
        realname = strip_name(realname)
        obj = SVCCommand() if is_svc_response(resp_helper) else CLICommand()
        obj.name = resolve_key_conflict(self.cmds, canonical_name(realname))
        pn = ''
        try:
            pn = getattr(self, 'realname')
        except AttributeError:
            pass
        obj.realname = pn + ' ' + realname if pn else realname
        obj.description = description
        obj.resp_helper = resp_helper
        self.cmds[obj.name] = obj
        return obj

    def __getattr__(self, name):
        obj = self.cmds.get(name)
        if obj is None:
            raise AttributeError(
                "'%s' object has no attribute '%s'" %
                (self.__class__.__name__, name))
        return obj

    def __dir__(self):
        return sorted(self.cmds.keys())


class CLISpec(CLIBase):
    '''The CLI specification'''

    def __init__(self):
        super(CLISpec, self).__init__()
        self.array_type = ''
        self.array_infos = []
        self.errors = []


class CLICommand(CLIBase):
    def __init__(self):
        super(CLICommand, self).__init__()
        self.name = ''
        self.realname = ''
        self.description = ''
        self.resp_helper = None
        self.params = OrderedDict()
        self.param_choices = []

    def add_param(
            self,
            realname,
            with_name=True,
            with_value=True,
            required=False,
            description='',
            options=None):
        param = CLIParam()
        param.realname = strip_name(realname)
        param.name = resolve_key_conflict(
            self.params, canonical_name(
                param.realname, replace_char=''))
        param.with_name = with_name
        param.with_value = with_value
        param.required = required
        param.description = description
        if options is None:
            options = []
        param.options = options
        self.params[param.name] = param
        return param

    def add_param_choice(self, params, required=False):
        if not params:
            raise CLISpecError(
                'ParamChoice should have at least one child element.')
        ch = CLIParamChoice(params, required)
        self.param_choices.append(ch)
        return ch

    @property
    def __doc__(self):
        doc = ['Help on %s(**kwargs): %s' % (self.name, self.description)]
        if self.realname:
            doc.append('It is wrapper for CLI "%s".' % self.realname)
        if self.params:
            doc.append('\nParameters:')
        for p in list(self.params.values()):
            doc.append('\t' + getattr(p, '__doc__', ''))
        if self.param_choices:
            doc.append('\nNotes:')
        for ch in self.param_choices:
            doc.append('\t' + getattr(ch, '__doc__', ''))
        return '\n'.join(doc)

    def process_args(self, kwargs):
        args = [self.realname]
        for p in list(self.params.values()):
            args.extend(p(kwargs))
        for ch in self.param_choices:
            ch(kwargs)
        return args, canonical_args(kwargs)

    def __call__(self, start_response, kwargs=None):
        '''Execute the command by calling `start_response`.

        :param start_response: The callable which accepts a str and a dict,
                               and returns an iterable yielding zero or
                               more string.
        :type start_response: callable
        :param kwargs: (optional) The command's parameters. Only the key
                                  defined by the command is accepted.
                       The key with prefix "pysvc." is reserved for internal
                       usage.

                       * pysvc.check_return_code: (bool) Indicates whether to
                       * check the return code, it is True by default.
                       * pysvc.escape: (bool) Indicates whether to escape
                       * special characters within the values of kwargs,
                       * it is True by default.
                       * pysvc.delim: (str) Field delimiter in a single
                       * character of command response (as csv format).
                       * It is computed You should not specify it.
                       * pysvc.flexible: (bool) Indicates whether to raise
                       * exception if response has error, it is False
                       * by default.
                       * pysvc.timeout: (float) Response timeout for each
                       * sending command in seconds.
                       * pysvc.with_header: (bool) Indicates whether
                       * the output has header.
        :type kwargs: dict
        :return: The response object.
        :rtype: :py:class:`pysvc.pysvc.unified.response.CLIResponse` or
                           the return value of `start_response`.
        '''
        if kwargs is None:
            kwargs = {}
        args, extra = self.process_args(kwargs)
        if not extra.get('flexible', False):
            for k in kwargs:
                if not k.startswith(
                        'xsf.') and k not in self.params and k != 'stdin':
                    raise CLISpecError(
                        'The parameter "%s" is not supported.' % k)
        if extra.pop('check_return_code', True):
            args.append(show_return_code_if_fail())
            extra['error_tag'] = TAG_ERR
        # if contains stdin input
        stdin_input = None
        if 'stdin' in list(kwargs.keys()):
            stdin_input = kwargs['stdin']
        # Retry when SVC return metadata service busy error
        attempt = 1
        while True:
            try:
                resp = start_response(' '.join(args), extra, stdin=stdin_input)
                # pylint: disable-msg=E1102
                if self.resp_helper:
                    resp = self.resp_helper(resp, extra)
                return resp
            except CLIFailureError as e:
                if e.returnCode != METADATA_RC_BUSY:
                    raise e
                else:
                    if attempt < RETRY_TIME:
                        attempt = attempt + 1
                        time.sleep(1)
                        continue
                    else:
                        raise e


class SVCCommand(CLICommand):
    __doc__ = CLICommand.__doc__  # must define explicitly

    def process_args(self, kwargs):
        args, pos_args = [self.realname], []
        delim = ''
        for p in list(self.params.values()):
            if p.realname == '-delim':
                args.append('-delim ,')
                delim = ','
            elif p.realname == '-nohdr':  # skip to prevent messing up output
                pass
            elif p.with_name:
                args.extend(p(kwargs))
            else:
                pos_args.extend(p(kwargs))
        for ch in self.param_choices:
            ch(kwargs)
        # Ignore document order to make positional arguments be last in SVC CLI
        args.extend(pos_args)
        extra = canonical_args(kwargs)
        if delim:
            extra['delim'] = delim
        return args, extra


class CLIParam(object):
    def __init__(self):
        super(CLIParam, self).__init__()
        self.realname = ''
        self.name = ''
        self.with_name = True
        self.with_value = True
        self.required = False
        self.description = ''
        self.options = []

    @property
    def __doc__(self):
        doc = ['%s:' % self.name]
        if self.required:
            doc.append('(Required)')
        if self.description:
            doc.append(self.description + '.')
        if self.with_value and self.options:
            doc.append('It should be one of "%s".' % self.options)
        return ' '.join(doc)

    def __call__(self, kwargs):
        '''Return a list of canonical arguments extracted from kwargs'''
        args = []
        if self.name not in kwargs:
            if self.required:
                raise CLISpecError(
                    'The parameter "%s" is missing.' %
                    self.name)
            return args
        if self.with_name:
            args.append(self.realname)
        if self.with_value:
            v = kwargs[self.name]
            if v is None:
                v = ''
            v = str(v)
            if self.options and v not in self.options:
                raise CLISpecError(
                    'The value of parameter "%s" should be one of "%s".' %
                    (self.name, self.options))
            args.append(
                escape_shell_arg(v) if kwargs.get(
                    'xsf.escape', True) else v)
        return args


class CLIParamChoice(object):
    def __init__(self, params=None, required=False):
        super(CLIParamChoice, self).__init__()
        if params is None:
            params = []
        self.params = params
        self.required = required

    @property
    def __doc__(self):
        if not self.params:
            return ''
        doc = ['Only one of' if self.required else 'None or only one of']
        doc.append(','.join(p.name for p in self.params))
        doc.append('can appear.')
        return ' '.join(doc)

    def __call__(self, kwargs):
        '''Check exclusive parameters in kwargs'''
        pass
        # num = len([p for p in self.params if p.name in kwargs])
        # if num > 1 or (num == 0 and self.required):
        #    raise CLISpecError('Only one of parameters "%s"
        #    can be specified.'%[p.name for p in self.params])


class SpecParserV20(object):
    '''Parser for the specification v2.0 '''

    def __init__(self, kwargs=None):
        super(SpecParserV20, self).__init__()
        if kwargs is None:
            kwargs = {}
        self.result = CLISpec()
        self.flexible = kwargs.get('flexible', False)

    def parse(self, tree):
        '''Parse CLI specification XML

        :param tree: The ElementTree object of CLI specification XML.
        :return: The CLI specification :py:class:`.CLISpec`.
        '''
        root = tree.getroot()
        if root.tag != 'ArraySyntax':
            self.die('ArraySyntax is missing.')
        tags = ['ArrayType', 'Errors', 'CompressedCommands', 'Commands']
        # It has good performance to traverse the tree and all its node only
        # once.
        for nd0 in root:
            if nd0.tag in tags:
                if nd0.tag == 'ArrayType' or nd0.tag == 'Errors':
                    tags.remove(nd0.tag)
                self.die_on_parse(nd0, nd0)
        if not (self.result.array_type and self.result.array_infos
                and self.result.errors):
            self.die('Some meta-data is missing.')
        return self.result

    def parse_ArrayType(self, nd):
        self.result.array_type = nd.get('type').strip()
        self.result.array_infos = [
            (nd0.get('type').strip(),
             nd0.get('version').strip()) for nd0 in etree_iterchildren(
                nd,
                tag='ArrayVersion')]

    def parse_Errors(self, nd):
        self.result.errors = to_text_list(etree_iterchildren(nd, tag='Error'))

    def parse_Commands(self, nd):
        resp0 = self.parse_Response(nd)
        names = [
            n0 for n0 in (
                n.strip() for n in nd.get(
                    'implements',
                    '').split(',')) if n0]
        for nd0 in etree_iterchildren(nd, tag='Executable'):
            self.die_on_parse(nd0, nd0, resp0, names)

    def parse_CompressedCommands(self, nd):
        if nd.text and nd.get(
                'compression',
                '') == 'zlib' and nd.get(
                'encoding',
                '') == 'base64':
            nd0 = etree.fromstring(extract_str(nd.text))
            if nd0.tag != 'Commands':
                self.die('Bad %s within CompressedCommands' % nd0.tag)
            implements = nd.get('implements', None)
            if implements is not None:
                nd0.set('implements', implements)
            self.parse_Commands(nd0)
        else:
            self.die('CompressedCommands format is not supported.')

    def parse_Executable(self, nd, resp=None, names=None):
        if names and nd.get('name', '').strip() not in names:
            return
        obj = self.result.add_cmd(
            nd.get('name'),
            nd.get(
                'description',
                ''),
            self.parse_Response(nd) or resp)
        # tgs1 and tgs2 are mutual exclusive
        tgs1, tgs2, notags = ['Command'], [
            'ValueParam', 'FlagParam', 'ParamChoice'], []
        for nd0 in nd:
            if nd0.tag in tgs1:
                tgs2 = notags
                self.die_on_parse(nd0, nd0, obj)
            elif nd0.tag in tgs2:
                tgs1 = notags
                self.die_on_parse(nd0, nd0, obj)

    def parse_Command(self, nd, target):
        obj = target.add_cmd(
            nd.get('name'),
            nd.get(
                'description',
                ''),
            self.parse_Response(nd) or target.resp_helper)
        for nd0 in nd:
            if nd0.tag in ('ValueParam', 'FlagParam', 'ParamChoice'):
                self.die_on_parse(nd0, nd0, obj)

    def parse_ValueParam(self, nd, target):
        return target.add_param(
            nd.get('name'), not to_bool(
                nd.get(
                    'noName', 'false')), True, to_bool(
                nd.get(
                    'required', 'false')), nd.get(
                        'description', ''), to_text_list(
                            etree_iterchildren(
                                nd, tag='Option')))

    def parse_FlagParam(self, nd, target):
        return target.add_param(
            nd.get('name'), True, False, to_bool(
                nd.get(
                    'required', 'false')), nd.get(
                'description', ''))

    def parse_ParamChoice(self, nd, target):
        ok = True
        params = []
        for nd0 in nd:
            if nd0.tag in ('ValueParam', 'FlagParam'):
                p = self.die_on_parse(nd0, nd0, target)
                if p:
                    p.required = False  # make children optional
                    params.append(p)
                else:
                    ok = False  # handle error in flexible mode
        return target.add_param_choice(params, to_bool(
            nd.get('required', 'false'))) if ok else None

    def parse_Response(self, parent):
        # 'Response' is always the first child or does not appear.
        # if parent is Commands, then pass the Commands name into
        # find_response_helper(), to deal with commands with special output
        for nd0 in parent:
            if nd0.tag == 'Response':
                if parent.tag == 'Command':
                    return find_response_helper(
                        nd0.get(
                            'type', None), parent.get(
                            'name', None))
                else:
                    return find_response_helper(
                        nd0.get(
                            'type', None), nd0.get(
                            'param', None))
            break

    def die_on_parse(self, nd, *args):
        return self.die(
            'Bad %s' %
            nd.tag,
            CLISpecError,
            getattr(
                self,
                'parse_%s' %
                nd.tag),
            args)

    def die(self, msg='', error=CLISpecError, callable_=None, args=None):
        if callable_:
            try:
                return callable_(*args) if args else callable_()
            except Exception as ex:  # we do not catch other BaseException
                if self.flexible:
                    xlog.exception('Continue in flexible mode.')
                else:
                    if not isinstance(ex, error):
                        xlog.exception('The error is re-raised as %s.' % error)
                        raise error(msg)
                    raise
        else:
            if self.flexible:
                xlog.error('Continue in flexible mode. %s' % msg)
            else:
                raise error(msg)


def strip_name(name):
    if name:
        name = name.strip()
    if not name:
        raise CLISpecError(
            'The name of Command or Executable or Param should not be empty.')
    return name


def canonical_name(name, maxlen=50, replace_char='_', prefix='C'):
    if isinstance(name, str):
        name = name.encode('ASCII', 'replace')
    if not name:
        name = prefix
    if isinstance(name, bytes):
        name = name.decode()
    name = re.sub(PATTERN_INVALID_CHAR, replace_char, name[:maxlen])
    if name.startswith('_'):
        return prefix + name
    elif name[0].isdigit():
        return prefix + '_' + name
    return name


def canonical_args(kwargs, prefix='xsf.'):
    idx = len(prefix)
    return dict((k[idx:], kwargs[k])
                for k in kwargs if k.startswith(prefix) and k != prefix)


def escape_shell_arg(data):
    if data and not data.isalnum():
        if not data.startswith("'"):
            data = "'" + data
        if not data.endswith("'"):
            data = data + "'"
    return data


def etree_iterchildren(element, tag=None):
    for ch in element.getchildren():
        if tag and tag == ch.tag:
            yield ch


def to_bool(value):
    if value == 'true':
        return True
    elif value == 'false':
        return False
    raise CLISpecError('"%s" is not boolean.' % value)


def to_text_list(nodes):
    return [nd.text.strip() for nd in nodes if nd.text is not None]


def resolve_key_conflict(dict_, key):
    if key in dict_:
        for suf in KEY_STR:
            newkey = '%s_%s' % (key, suf)
            if newkey not in dict_:
                return newkey
        raise CLISpecError('Too many conflicts for the key "%s".' % key)
    else:
        return key


def show_return_code_if_fail(tag=TAG_ERR):
    return '|| echo %s $?' % tag


def extract_str(value):
    if isinstance(value, str):
        value = value.encode()
    return zlib.decompress(base64.decodebytes(value))


def compress_str(value):
    return base64.encodebytes(zlib.compress(value))


def parse(source, **kwargs):
    '''Parse CLI specification XML.

    :param source: The XML of CLI specification.
    :type source: str for file name of XML or an object which has read()
                  method, e.g. StringIO.
    :param flexible: (optional) ndicates whether to enable flexible mode which
                                bypasses strict error checking, it is False by
                                default.
    :type flexible: bool
    :return: The CLI specification.
    :rtype: :py:class:`.CLISpec`
    :raise CLISpecError: Can occur if the XML is not valid.

    Example:

    >>> from pysvc.pysvc.unified.clispec import parse
    >>> parse('clispec-sample-2.0.xml')
    <pysvc.pysvc.unified.clispec.CLISpec object at 0x...>
    '''
    try:
        tree = etree.parse(source)
        ver = tree.getroot().get('version', None)
    except XMLException as ex:
        raise CLISpecError('The CLI spec is not valid XML.', ex)
    if 'flexible' in kwargs and ver != '2.0':
        xlog.error(
            'The CLI spec %s is not supported. Continue in flexible mode.' %
            ver)
        ver = '2.0'
    if ver == '2.0':
        spec = SpecParserV20(kwargs).parse(tree)
        tree.getroot().clear()
        if hasattr(source, 'close'):
            source.close()
        return spec
    raise CLISpecError('The CLI spec %s is not supported.' % ver)
