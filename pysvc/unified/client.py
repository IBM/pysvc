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
'''Unified SSH client for IBM Spectrum Virtualize Family Storage'''

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import pkg_resources
from logging import getLogger
import pysvc.errors as ce
from pysvc.messages import UnifiedMessages
from pysvc.transports.ssh_transport import SSHTransport
from pysvc.unified.clispec import parse
from pysvc import PYSVC_DEFAULT_LOGGER
from .scp_cli_client import ScpClient
from pysvc.unified.helpers import etree
from pysvc.unified.helpers.xml_util import XMLException

__all__ = ['connect']

xlog = getLogger(PYSVC_DEFAULT_LOGGER)


class IncorrectDeviceTypeError(ce.UnableToConnectException):
    '''Raise if the expected device type is not found.'''
    pass


class NoSpecificationError(ce.UnableToConnectException):
    '''Raise if no CLI specification is found for the storage array.'''
    pass


class UnifiedSSHClient(object):
    '''Unified SSH client for IBM Spectrum Virtualize Family Storage.

    It creates callable stubs for the CLI commands of storage array.
    The stub is implemented as :py:class:`.Proxy` for
    :py:class:`pysvc.pysvc.unified.clispec.CLICommand`.
    '''

    def __init__(self):
        super(UnifiedSSHClient, self).__init__()
        self.transport = None
        self.specification = None
        self.flexible = False

    def close(self):
        '''Close the connection.'''
        if self.transport:
            self.transport.disconnect()
            self.transport = None
        self.specification = None

    def send_raw_command(self, cmd, extra=None, stdin=None):
        '''Send plain string as command to storage array and execute.

        :param cmd: The command.
        :type cmd: str
        :param extra: (optional) The extra parameters.

                      * timeout: (float) Response timeout for each sending
                        command in seconds.
        :type extra: dict
        :return: The content from stdout and stderr of the executed command.
        :rtype: tuple
        '''
        timeout = extra.get('timeout', 0) if extra else 0
        xlog.debug("+++{0}+++".format(cmd))
        _, stdout, stderr = self.transport.send_command(
            cmd, raw=True, timeout=timeout, stdin_input=stdin)
        return stdout, stderr

    def get_device_info(self):
        '''Get the device information of storage array.

        :return: The device type and version.
        :rtype: tuple
        '''
        return (self.specification.array_type,
                self.specification.array_infos) if self.specification else None

    def get_dump_element_tree(self, remote_path, timeout=None):
        """
        get the element tree of xml remote_path specified
        :param remote_path: full path on the SVC,
               e.g. /dumps/iostats/Nn_stats_151240_151120_162817
        :param timeout: int, the timeout of the session
        :return: ElementTree
        """
        raw_xml = self.get_dump(remote_path, timeout)
        try:
            return etree.parse(StringIO(raw_xml))
        except XMLException as ex:
            err_msg = (r'The dump file context is not valid XML: {}'
                       .format(raw_xml))
            xlog.error(err_msg)
            raise ex(err_msg)

    def get_dump(self, remote_path, timeout=None):
        """
        :param remote_path: full path on the SVC,
               e.g. /dumps/iostats/Nn_stats_151240_151120_162817
        :param timeout: int, the timeout of the session
        :return: str, the context of the file
        """
        scp_client = ScpClient(self.transport.transport.get_transport(),
                               timeout)
        return scp_client.receive(remote_path)

    def __getattr__(self, name):
        obj = getattr(self.specification, name, None)
        if obj is None:
            raise AttributeError(
                "'%s' object has no attribute '%s'" %
                (self.__class__.__name__, name))
        return Proxy(obj, self.send_raw_command)

    def __dir__(self):
        return dir(self.specification)


class Proxy(object):
    '''Proxy for CLI command

    Read __doc__ attribute to get document instead of
    using __builtins__.help(), e.g.

    >>> print a_proxy.__doc__
    Help on ...
    '''

    def __init__(self, referent, context):
        super(Proxy, self).__init__()
        self.referent = referent
        self.context = context

    @property
    def __doc__(self):
        return getattr(self.referent, '__doc__', None)

    def __getattr__(self, name):
        at = getattr(self.referent, name, None)
        if at is None:
            raise AttributeError(
                "'%s' object has no attribute '%s'" %
                (self.__class__.__name__, name))
        return Proxy(at, self.context)

    def __dir__(self):
        return dir(self.referent)

    def __call__(self, **kwargs):
        '''Call the wrapped referent with given parameters and
           return the result.'''
        return self.referent(self.context, kwargs)


def yield_device_type(conn):
    conn.specification, oldspec = parse_cli_spec(
        conn, get_cli_spec('xsf', '1.0')), conn.specification
    try:
        try:
            for clu in conn.cli.lscluster():
                device = 'ifs' if clu.get('Profile') == 'IFS' else 'sonas'
                for nd in conn.cli.lsnode(cluster=clu.get('Name')):
                    yield device, canonical_version(
                        nd.get('Product Version', '')
                        or nd.get('Product version', '')
                        or nd.get('product version', ''))
        except GeneratorExit:
            raise
        except Exception:
            xlog.exception('No IFS or SoNAS is found, and continue.')
        try:
            for clu in conn.svcinfo.lscluster():
                if clu.get('location') == 'local':
                    for clu1 in conn.svcinfo.lscluster(cluster=clu.get('id')):
                        yield 'svc', canonical_version(
                            clu1.get('code_level', ''))
        except GeneratorExit:
            raise
        except Exception:
            xlog.exception('No SVC or Storwize is found, and continue.')
    finally:
        conn.specification = oldspec


def set_specification(conn, with_remote_clispec=True):
    spec = get_remote_cli_spec(conn) if with_remote_clispec else None
    if not spec:
        xlog.info(UnifiedMessages.UNIFIED_PARSE_LOCAL_START)
        for d, t in yield_device_type(conn):
            try:
                spec = parse_cli_spec(conn, get_cli_spec(d, t))
            except Exception:
                xlog.exception(
                    'No CLI specification found for "%s, %s", and continue.' %
                    (d, t))
            if spec:
                break
    if not spec:
        raise NoSpecificationError(UnifiedMessages.UNIFIED_NO_CLI_SPEC)
    conn.specification = spec


def check_device_type(conn, device_type):
    if not device_type:
        return
    info = conn.get_device_info()
    if not info or info[0] != device_type:
        raise IncorrectDeviceTypeError(
            UnifiedMessages.UNIFIED_INCORRECT_DEVICE_TYPE(device_type))


def get_remote_cli_spec(conn):
    try:
        stdout, stderr = conn.send_raw_command('catxmlspec')
        if stdout:
            return parse_cli_spec(conn, StringIO(stdout.decode()))
        xlog.warning(UnifiedMessages.UNIFIED_CATXMLSPEC_FAIL(stderr))
    except Exception:
        xlog.exception(UnifiedMessages.UNIFIED_PARSE_REMOTE_FAIL)


def parse_cli_spec(conn, source):
    spec = parse(source, flexible=conn.flexible)
    # make sure there is CLI command defined in CLI spec
    return spec if spec and spec.cmds else None


def device_type_alias(device, version):
    if device in ('storwize', 'storwise'):
        device = 'svc'
    if device == 'svc':
        if version.startswith('6.') and version not in ('6.1', '6.2', '6.3'):
            version = '6.3'
    return device, version


def get_cli_spec(device, version):
    # pylint: disable-msg=E1101
    return pkg_resources.resource_stream(
        __name__, '%s-%s.xml' %
        device_type_alias(
            device, version))


def canonical_version(data):
    return '.'.join(data.strip().split('.')[:2])


def connect(address, **kwargs):
    '''Connect to storage array through SSH.

    :param address: The IP address or host name of storage array.
    :type address: str
    :param username: (optional) The username of login account.
    :type username: str
    :param password: (optional) The password of login account or private key.
    :type password: str
    :param port: (optional) The port of SSH service in storage array,
                            it is 22 by default.
    :type port: int
    :param privatekey: (optional) The private key of login account.
    :type privatekey: str
    :param privatekey_filename: (optional) The file name of private key.
    :type privatekey_filename: str
    :param add_hostkey: (optional) Indicates whether to add SSH host key of
           storage array to known hosts, it is True by default.
    :type add_hostkey: bool
    :param timeout: (optional) Connection timeout in seconds,
                               it is 30 by default.
    :type timeout: int
    :param cmd_timeout: (optional) Response timeout for each sending command
                                   in seconds, it is 60.0 by default.
    :type cmd_timeout: float
    :param device_type: (optional) The device type of storage array, e.g.
                                   "svc", "storwize", None.
    :type device_type: str
    :param flexible: (optional) Indicates whether to enable flexible mode
                                which bypasses strict error checking, it is
                                False by default.
    :type flexible: bool
    :param with_remote_clispec: (optional) Indicates whether to read CLI
                                           specification from remote storage
                                           array, it is True by default.
    :type with_remote_clispec: bool
    :return: The connection object to storage array.
    :rtype: :py:class:`.UnifiedSSHClient`

    Example:

    >>> connect('ip', username='admin', privatekey_filename=r'/local/key')
    <pysvc.pysvc.unified.client.UnifiedSSHClient object at 0x...>
    '''
    g = kwargs.get
    trans = SSHTransport(
        host=address,
        user=g('username'),
        password=g('password'),
        port=g(
            'port',
            22),
        auto_add=g(
            'add_hostkey',
            True),
        pkey=g('privatekey'),
        pkey_file=g('privatekey_filename'),
        timeout=g(
            'timeout',
            30),
        cmd_timeout=g(
            'cmd_timeout',
            60.0))
    conn = UnifiedSSHClient()
    try:
        trans.connect()
        conn.flexible = g('flexible', False)
        conn.transport = trans
        set_specification(conn, g('with_remote_clispec', True))
        check_device_type(conn, g('device_type'))
        return conn
    except BaseException:
        trans.disconnect()
        conn.close()
        raise
