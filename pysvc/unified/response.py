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
'''Parsers for CLI response'''

import csv
from functools import reduce
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

try:
    long
except NameError:
    long = int

try:
    basestring
except NameError:
    basestring = str

from munch import Munch
from logging import getLogger
import pysvc.errors as ce
from pysvc import PYSVC_DEFAULT_LOGGER

__all__ = ['find_response_helper']

DEFAULT_DELIM = '\t'
xlog = getLogger(PYSVC_DEFAULT_LOGGER)


class CLIFailureError(ce.StorageArrayClientException):
    '''Raise if CLI fails.'''

    def __init__(self, message=None, original_exception=None, returnCode=-1):
        ce.StorageArrayClientException.__init__(
            self, message, original_exception=None)
        self.returnCode = returnCode


class CLIResponse(object):
    '''Iterable for CLI response.

    Example:

    >>> resp
    <pysvc.pysvc.unified.response.CLIResponse object at 0x...>
    >>> for part in resp:
    ...     print part
    ...
    Bunch(..., name = 'a', ...)
    Bunch(..., name = 'b', ...)
    >>>
    >>> list(resp) # or resp.as_list
    [Bunch(..., name = 'a', ...), Bunch(..., name = 'b', ...)]
    >>>
    >>> resp.as_single_element
    Bunch(..., name = ['a', 'b'], ...)
    >>>
    >>> resp.as_dict('name')
    Bunch(a = Bunch(..., name = 'a', ...), b = Bunch(..., name = 'b', ...))
    '''

    def __init__(self, resp, kwargs=None):
        super(CLIResponse, self).__init__()
        if kwargs is None:
            kwargs = {}
        self.response = resp
        try:
            self.result = self.parse(resp, kwargs)
        except Exception:
            if kwargs.get('flexible', False):
                self.result = tuple()
                xlog.exception(
                    'Fail to parse CLI output, but continue in flexible mode.')
            else:
                raise

    def parse(self, resp, kwargs):
        if isinstance(resp, basestring):
            stdout, stderr = resp, ''
        else:
            stdout, stderr = resp
        if isinstance(stdout, bytes):
            stdout = stdout.decode()
        if isinstance(stderr, bytes):
            stderr = stderr.decode()
        stdout = stdout.lstrip()  # remove starting space to work with csv
        stdoutlines = stdout.splitlines()

        # e.g. if stdout is "<error_tag> 4", the return code is 4
        error_tag = kwargs.get('error_tag', '')
        if error_tag:
            for line in stdoutlines:
                idx = line.find(error_tag)
                if idx >= 0:
                    rc = ' '.join(
                        tk for tk in line[idx + len(error_tag):].split()
                        if tk.isdigit() or tk.startswith('-')
                        and tk[1:].isdigit())
                    try:
                        returnCode = int(rc)
                    except Exception as e:
                        xlog.error(e)
                        returnCode = -1
                    raise CLIFailureError(
                        'CLI failure. Return code is %s. '
                        'Error message is "%s"' % (rc, stderr),
                        returnCode=returnCode)

        delim = kwargs.get('delim', DEFAULT_DELIM)

        result = []
        snif = MySniffer(delim)
        rd = csv.reader(stdoutlines, snif.sniff(stdout))
        with_header = kwargs.get('with_header', None)
        if with_header is None:
            with_header = snif.has_header(stdout)
        if with_header:
            hds = next(rd) if stdout else ''

            xlog.debug("+++++ {0}".format(hds))
            if (len(hds) > 0) and (hds[0].find(
                    'CMMVC7017E Login has failed') == 0):
                error_msg = ('CLI failure. Return code is 1. '
                             'Error message is "{0}"'.format(hds[0]))
                xlog.error(error_msg)
                xlog.debug("+++++ STDOUT: \n{0}".format(stdout))
                xlog.debug("+++++ STDERR: \n{0}".format(stderr))
                raise CLIFailureError(error_msg, returnCode=1)

            for row in rd:
                cur = Munch()
                for k, v in zip(hds, row):
                    append_dict(cur, k, v, strip=True)
                result.append(cur)
        else:
            cur = Munch()
            for row in rd:
                if row:
                    append_dict(cur, row[0], ' '.join(row[1:]), strip=True)
                elif cur:  # start new section
                    result.append(cur)
                    cur = Munch()
            if cur:
                result.append(cur)
        return result

    def __iter__(self):
        return iter(self.result)

    @property
    def as_single_element(self):
        '''Return response to a single dict like object
           :py:class:`xiv.dtypes.Bunch` or None.'''
        return reduce(
            merge_dict,
            self.result,
            Munch()) if self.result else None

    @property
    def as_list(self):
        '''Return response as a list of :py:class:`xiv.dtypes.Bunch`.'''
        return self.result[:]

    def as_dict(self, key):
        '''Return response which has the key to a dict like
           object :py:class:`xiv.dtypes.Bunch`.'''
        res = Munch()
        _ = [append_dict(res, a[key], a) for a in self.result if key in a]
        return compact_dict(res)


class SVCResponse(CLIResponse):
    resp_type = 'svc'


class svcinfo_lsroute_response(SVCResponse):
    def parse(self, resp, kwargs):
        if isinstance(resp, basestring):
            stdout, stderr = resp, ''
        else:
            stdout, stderr = resp
        if isinstance(stdout, bytes):
            stdout = stdout.decode()
        if isinstance(stderr, bytes):
            stderr = stderr.decode()
        if not kwargs.get('delim', None):
            kwargs['delim'] = ' '

        def sections():
            cur = []
            for line in stdout.splitlines():
                if 'routing table' in line:
                    if cur:
                        cur[0:1] = [cur[0].replace(' Next Hop ', ' Next_Hop ')]
                        yield ('\n'.join(cur), stderr)
                        cur = []
                else:
                    line = line.strip()
                    if line:
                        cur.append(line)
            if cur:
                cur[0:1] = [cur[0].replace(' Next Hop ', ' Next_Hop ')]
                yield ('\n'.join(cur), stderr)
        return [d for sec in sections()
                for d in SVCResponse.parse(self, sec, kwargs)]

# response helper to parse vvolmd_entry_create, vvolmd_entry_update,
# vvolmd_entry_retrieve command#


class svctask_metadata_entry_response(SVCResponse):
    def parse(self, resp, kwargs):
        if isinstance(resp, basestring):
            stdout, stderr = resp, ''
        else:
            stdout, stderr = resp
        if isinstance(stdout, bytes):
            stdout = stdout.decode()
        if isinstance(stderr, bytes):
            stderr = stderr.decode()
        stdout = stdout.lstrip()  # remove starting space to work with csv
        stdoutlines = stdout.splitlines()

        # e.g. if stdout is "<error_tag> 4", the return code is 4
        error_tag = kwargs.get('error_tag', '')
        if error_tag:
            for line in stdoutlines:
                idx = line.find(error_tag)
                if idx >= 0:
                    rc = ' '.join(tk for tk in
                                  line[idx + len(error_tag):].split() if
                                  tk.isdigit() or tk.startswith('-')
                                  and tk[1:].isdigit())
                    raise CLIFailureError(
                        'CLI failure. Return code is %s. Error message '
                        'is "%s"' % (rc, stderr), returnCode=int(rc))

        # start to deal with raw response
        result = []
        # entry create, update
        if len(stdoutlines) == 1:
            result.append(colon2Bunch(stdoutlines[0]))
        # entry retrieve
        elif len(stdoutlines) > 1:
            entry = colon2Bunch(stdoutlines[0])
            stdoutlines.pop(0)
            idx = stdout.find('\n')
            entry['content'] = stdout[idx + 1:]
            result.append(entry)
        return result


# response helper to parse vvolmd_entry_list command#
class svctask_metadata_entry_list_response(SVCResponse):
    def parse(self, resp, kwargs):
        if isinstance(resp, basestring):
            stdout, stderr = resp, ''
        else:
            stdout, stderr = resp
        if isinstance(stdout, bytes):
            stdout = stdout.decode()
        if isinstance(stderr, bytes):
            stderr = stderr.decode()
        stdout = stdout.lstrip()  # remove starting space to work with csv
        stdoutlines = stdout.splitlines()

        # e.g. if stdout is "<error_tag> 4", the return code is 4
        error_tag = kwargs.get('error_tag', '')
        if error_tag:
            for line in stdoutlines:
                idx = line.find(error_tag)
                if idx >= 0:
                    rc = ' '.join(tk for tk in
                                  line[idx + len(error_tag):].split()
                                  if tk.isdigit() or tk.startswith('-')
                                  and tk[1:].isdigit())
                    raise CLIFailureError(
                        'CLI failure. Return code is %s. Error message '
                        'is "%s"' % (rc, stderr), returnCode=int(rc))

        # start to deal with raw response
        result = []
        try:
            if len(stdoutlines) < 1:
                return result
            label = stdoutlines.pop(0)
            label = label.split()
            for line in stdoutlines:
                entry = Munch()
                line_entry = line.split()
                for i in [0, 1, 2]:
                    entry[label[i]] = line_entry[i]
                result.append(entry)
        except Exception:
            raise CLIFailureError('Fail to parse the CLI response :' + stdout)
            return result
        return result


# response helper to parse lsmetadatavdisk command#
class svcinfo_lsmetadatavdisk_response(SVCResponse):
    def parse(self, resp, kwargs):
        if isinstance(resp, basestring):
            stdout, stderr = resp, ''
        else:
            stdout, stderr = resp
        if isinstance(stdout, bytes):
            stdout = stdout.decode()
        if isinstance(stderr, bytes):
            stderr = stderr.decode()
        stdout = stdout.lstrip()  # remove starting space to work with csv
        stdoutlines = stdout.splitlines()

        # e.g. if stdout is "<error_tag> 4", the return code is 4
        error_tag = kwargs.get('error_tag', '')
        if error_tag:
            for line in stdoutlines:
                idx = line.find(error_tag)
                if idx >= 0:
                    rc = ' '.join(tk for tk in
                                  line[idx + len(error_tag):].split() if
                                  tk.isdigit() or tk.startswith('-')
                                  and tk[1:].isdigit())
                    raise CLIFailureError(
                        'CLI failure. Return code is %s. Error message '
                        'is "%s"' % (rc, stderr), returnCode=int(rc))

        # start to deal with raw response
        result = []
        result.append(lines2Bunch(stdoutlines))
        return result

# response helper to parse vvolmd_db_list command


class svctask_metadata_db_list_response(SVCResponse):
    def parse(self, resp, kwargs):
        if isinstance(resp, basestring):
            stdout, stderr = resp, ''
        else:
            stdout, stderr = resp
        if isinstance(stdout, bytes):
            stdout = stdout.decode()
        if isinstance(stderr, bytes):
            stderr = stderr.decode()
        stdout = stdout.lstrip()  # remove starting space to work with csv
        stdoutlines = stdout.splitlines()

        # e.g. if stdout is "<error_tag> 4", the return code is 4
        error_tag = kwargs.get('error_tag', '')
        if error_tag:
            for line in stdoutlines:
                idx = line.find(error_tag)
                if idx >= 0:
                    rc = ' '.join(tk for tk in
                                  line[idx + len(error_tag):].split() if
                                  tk.isdigit() or tk.startswith('-') and
                                  tk[1:].isdigit())
                    raise CLIFailureError(
                        'CLI failure. Return code is %s. Error message '
                        'is "%s"' % (rc, stderr), returnCode=int(rc))

        result = []
        try:
            if len(stdoutlines) < 1:
                return result
            label = stdoutlines.pop(0)
            label = label.split()
            for line in stdoutlines:
                entry = Munch()
                line_entry = line.split()
                for i in [0]:
                    entry[label[i]] = line_entry[i]
                result.append(entry)
        except Exception:
            raise CLIFailureError('Fail to parse the CLI response :' + stdout)
            return result
        return result


class MySniffer(csv.Sniffer):
    def __init__(self, delim):
        csv.Sniffer.__init__(self)
        self.delim = delim

    def sniff(self, sample, delimiters=None):
        class dialect(csv.Dialect):
            delimiter = self.delim
            quotechar = '"'
            doublequote = True
            skipinitialspace = True
            lineterminator = '\r\n'
            quoting = csv.QUOTE_MINIMAL
        return dialect

    def has_header(self, sample):
        ss = StringIO(sample)
        try:
            return self._has_header(csv.reader(ss, self.sniff(sample)))
        except Exception:
            xlog.exception('Can not detect header, and continue.')
        finally:
            ss.close()
        return False

    def _has_header(self, rdr):
        try:
            header = next(rdr)
        except StopIteration:
            return False
        columns = len(header)
        coltypes = {}
        rows = [row for row in rdr if len(row) == columns][:20]
        for col in range(columns):
            if all(is_numeric(row[col]) for row in rows):
                coltypes[col] = int
            elif len(set(len(row[col]) for row in rows)
                     ) == 1:  # all cells in column have same length
                coltypes[col] = len(rows[0][col])
        hasHeader = 0
        for col, tp in list(coltypes.items()):
            if tp is int:
                hasHeader += -1 if is_numeric(header[col]) else 1
            else:
                hasHeader += -1 if len(header[col]) == tp else 1
        return hasHeader > 0


def compare_similar(data1, data2, factor=2):
    '''Return True if most of keys in both data are same, otherwise False'''
    la, lb = len(data1), len(data2)
    lc = len(set(data1.keys()).intersection(set(data2.keys()))) * factor
    return lc >= max(la, lb)


def append_dict(dict_, key, value, strip=False):
    if strip:
        key, value = key.strip() if isinstance(
            key, basestring) else key, value.strip() if isinstance(
            value, basestring) else value
    obj = dict_.get(key, None)
    if obj is None:
        dict_[key] = value
    elif isinstance(obj, list):
        obj.append(value)
        dict_[key] = obj
    else:
        dict_[key] = [obj, value]
    return dict_


def compact_dict(dict_):
    for k, v in list(dict_.items()):
        if isinstance(v, list) and v:
            for a, b in zip(v, v[1:]):
                if a != b:
                    break
            else:  # if all members are same
                dict_[k] = v[0]
    return dict_


def merge_dict(dict1, dict2):
    for k, v in list(dict2.items()):
        append_dict(dict1, k, v)
    return compact_dict(dict1)


def compact_if_not_similar(dicts):
    for a, b in zip(dicts, dicts[1:]):
        # if some data are not similar, they are aspects of the same object,
        # so merge all data
        # e.g. "svcinfo lsvdisk 1"
        if not compare_similar(a, b):
            return [reduce(merge_dict, dicts, Munch())]
    # if all data are similar, they are for different objects, so no merge
    # e.g. "svcinfo lsportip 1"
    return dicts


def is_numeric(data):
    for t in (to_long_hex, float):
        try:
            t(data)
            return True
        except (ValueError, OverflowError):
            pass
    return False

# " Token: 1234 TimeStamp: 20141013" =>
# Bunch(Token='1234',TimeStamp='20141013')


def colon2Bunch(line=''):
    ret = Munch()
    pairs = line.split()
    i = 0
    while i < len(pairs):
        if pairs[i].endswith(':'):
            ret[pairs[i].replace(':', '')] = pairs[i + 1]
            i = i + 2
    return ret

# ["accesspath /mnt/file","vdisk_id    1"] =>
# Bunch(accesspath='/mnt/file',vdisk_id='1')


def lines2Bunch(lines=[]):
    ret = Munch()
    for line in lines:
        pairs = line.split()
        i = 0
        while i < len(pairs):
            ret[pairs[i]] = pairs[i + 1]
            i = i + 2
    return ret


def to_long_hex(data):
    return long(data, 16)


def is_svc_response(name):
    return getattr(name, 'resp_type', None) == 'svc' or (
        isinstance(name, basestring) and name.startswith('svc'))


def find_response_helper(name, param=None):
    '''Find CLI response helper.

    :param name: The name of CLI response type. It has "svc" prefix for
                 SVC CLI.
    :type name: str
    :param param: (optional) Extra parameter.
    :type param: str
    '''
    if is_svc_response(name):
        if param in [
            'metadata_entry_create',
            'metadata_entry_update',
                'metadata_entry_retrieve']:
            return svctask_metadata_entry_response
        elif param == 'metadata_entry_list':
            return svctask_metadata_entry_list_response
        elif param == 'metadata_db_list':
            return svctask_metadata_db_list_response
        elif param == 'lsmetadatavdisk':
            return svcinfo_lsmetadatavdisk_response
        elif param == 'lsroute':
            return svcinfo_lsroute_response
        else:
            return SVCResponse
