##############################################################################
# Copyright 2025 IBM Corp.
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
'''Test for unified SSH client'''

import os
import sys
import traceback
import unittest
from unittest import TestCase
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

import mock
from nose.plugins.attrib import attr
from pysvc.unified import connect
import pysvc.unified.client as uc
import pysvc.unified.clispec as ucs
import pysvc.unified.response as ucr
from pysvc.unified.response import MySniffer
from pysvc.unified.client import UnifiedSSHClient
from pysvc.unified import client
from .testdata import *

ADDR_SVC = '9.115.247.60'
TEST_ROOT = os.path.dirname(os.path.abspath(__file__))


def getpath(name):
    return os.path.abspath(os.path.join(TEST_ROOT, name))


def nothing(value, _=None, stdin=None):
    return value


class FakeResponse(object):

    def __init__(self, resp_type):
        super(FakeResponse, self).__init__()
        self.resp_type = resp_type

    def __call__(self, resp, kwargs):
        return resp


class TestUtilMixin:

    def assertRaisesEx(self, excClass, callableObj, *args, **kwargs):
        try:
            callableObj(*args, **kwargs)
        except excClass:
            traceback.print_exc(file=sys.stdout)
            return
        else:
            if hasattr(excClass, '__name__'):
                excName = excClass.__name__
            else:
                excName = str(excClass)
            raise self.failureException("%s not raised" % excName)


class TestUnifiedSSHClient(TestCase):

    def setUp(self):
        self.ssh_transport_patcher = mock.patch(
            r'pysvc.unified.tests.'
            r'test_unified_client.client.SSHTransport')
        self.ssh_transport_patcher.start()
        self.set_specification_patcher = mock.patch(
            r'pysvc.unified.tests.test_unified_client.client.'
            r'set_specification'
        )
        self.set_specification_patcher.start()
        self.check_device_type_patcher = mock.patch(
            r'pysvc.unified.tests.test_unified_client.client.'
            r'check_device_type')
        self.check_device_type_patcher.start()
        self.conn = connect(
            r'test address',
            username=r'admin',
            password=r'password'
        )

    def tearDown(self):
        self.ssh_transport_patcher.stop()
        self.set_specification_patcher.stop()
        self.check_device_type_patcher.stop()

    @mock.patch.object(UnifiedSSHClient, 'get_dump', mock.MagicMock(
        return_value=r'<test></test>'))
    @attr("integration_test")
    def test_get_dump_element_tree(self):
        res = self.conn.get_dump_element_tree(r'test path')
        self.assertEqual(res.getroot().tag, r'test')

    @mock.patch('pysvc.unified.tests.test_unified_client.client.ScpClient')
    @attr("integration_test")
    def test_get_dump(self, scp_client_mock):
        self.conn.get_dump(r'test path')
        scp_client_mock.return_value.receive.assert_called_with(r'test path')


class TestUnifiedSSHClientSVC(TestCase, TestUtilMixin):

    @mock.patch.object(uc, 'yield_device_type', mock.Mock(
        return_value=[('svc', '6.2')]))
    def setUp(self):
        self.conn = connect(ADDR_SVC, username='testuser', password='passw0rd')

    def tearDown(self):
        self.conn.close()

    @attr("integration_test")
    def test_connect(self):
        conn = self.conn
        out, err = conn.send_raw_command('svcinfo lscluster')
        self.assertFalse(err, 'CLI fails:\n%s' % err)
        self.assertRaises(ucr.CLIFailureError,
                          conn.svcinfo.lshost, host='notexists')
        self.assertRaises(ucr.CLIFailureError,
                          conn.svcinfo.lshost, host_id='notexists')
        self.assertRaises(ucr.CLIFailureError,
                          conn.svcinfo.lshost, host_name='notexists')
        self.assertRaises(ucs.CLISpecError, conn.svcinfo.lsvdiskhostmap,
                          id='notexists')
        self.assertRaises(ucr.CLIFailureError,
                          conn.svcinfo.lsvdiskhostmap, vdisk='notexists')
        self.assertRaises(ucr.CLIFailureError,
                          conn.svcinfo.lsvdiskhostmap, vdisk_id='notexists')
        self.assertRaises(ucr.CLIFailureError,
                          conn.svcinfo.lsvdiskhostmap, vdisk_name='notexists')

    @attr("integration_test")
    def test_close(self):
        self.assertTrue(self.conn.svcinfo)
        self.conn.close()
        self.assertFalse(getattr(self.conn, 'svcinfo', None))

    @attr("integration_test")
    def test_get_device_info(self):
        self.assertEqual(('svc', [('svc', '1.5.a')]),
                         self.conn.get_device_info())

    @mock.patch.object(uc, 'yield_device_type',
                       mock.Mock(return_value=[('svc', '6.2')]))
    @attr("integration_test")
    def test_device_type(self):
        self.tearDown()
        self.conn = connect(ADDR_SVC, username='testuser', password='passw0rd')
        self.assertTrue(self.conn)
        self.assertRaisesEx(uc.IncorrectDeviceTypeError, connect, ADDR_SVC,
                            username='testuser', password="passw0rd",
                            device_type='storwize')

    @attr("integration_test")
    def test_set_specification(self):
        self.tearDown()
        self.conn = connect(ADDR_SVC, username='testuser', password='passw0rd')
        self.assertTrue(list(self.conn.svcinfo.lscluster()))
        self.assertTrue(list(self.conn.svcinfo.lsuser()))
        self.assertTrue(list(self.conn.svcinfo.lsmdiskgrp()))
        expect_ = list(self.conn.svcinfo.lsmdiskgrp())
        self.assertTrue(expect_[0].name)
        self.assertTrue(expect_[0].capacity)

    @attr("integration_test")
    def test_error_code(self):
        try:
            self.conn.svcinfo.lscluster(cluster='never_exists')
        except ucr.CLIFailureError as ex:
            expect_ = 'CLI failure. Return code is 1. Error message ' \
                      'is "CMMVC5804E The action failed because an ' \
                      'object that was specified in the command does ' \
                      'not exist.\n"'
            self.assertEqual(expect_, ex.my_message)
            return
        self.assertTrue(False, 'No exception raised.')

        res = self.conn.svcinfo.lscluster(
            **{'cluster': 'never_exists', 'xsf.check_return_code': False})
        self.assertEqual([], res.result)

        res = self.conn.svcinfo.lscluster(
            **{'cluster': 'never_exists', 'xsf.flexible': True})
        self.assertEqual(tuple(), res.result)

    @attr("integration_test")
    def test_doc(self):
        self.maxDiff = None
        expect_ = r'''Help on svcinfo(**kwargs): 
It is wrapper for CLI "svcinfo".'''
        self.assertEqual(expect_, self.conn.svcinfo.__doc__)

        expect_ = r'''Help on svctask(**kwargs): 
It is wrapper for CLI "svctask".'''
        self.assertEqual(expect_, self.conn.svctask.__doc__)

        expect_ = r'''Help on lscluster(**kwargs): Displays system information.
It is wrapper for CLI "svcinfo lscluster".

Parameters:
	nohdr:
	delim:
	bytes:
	filtervalue:
	cluster:
	cluster_id:
	cluster_name:
	object_id:

Notes:
	None or only one of cluster,cluster_id,cluster_name,object_id can appear.'''
        self.assertEqual(expect_, self.conn.svcinfo.lscluster.__doc__)

        expect_ = r'''Help on mkvdisk(**kwargs): Creates a sequential, striped, or image mode volume.
It is wrapper for CLI "svctask mkvdisk".

Parameters:
	accessiogrp:
	autoexpand:
	blocksize:
	cache: readwrite|none.
	easytier: on|off.
	iogrp:
	mdisk:
	mdiskgrp: (Required)
	mirrorwritepriority: latency|redundancy.
	name:
	node:
	open_access_scsi_id: open access scsi id.
	rsize: disk_size|disk_size_percentage%|auto.
	size:
	tier: tier0_flash | tier1_flash | tier_enterprise | tier_nearline.
	unit: b|kb|mb|gb|tb|pb.
	warning: disk_size|disk_size_percentage%.
	grainsize: 8|32|64|128|256.
	import:
	fmtdisk:
	nofmtdisk:
	grainsize_0: 8|32|64|128|256.
	import_0:
	nofmtdisk_0:
	grainsize_1: 8|32|64|128|256.
	import_1:
	createsync:
	uuid:
	instance:
	instance840:
	grainsize_2: 8|32|64|128|256.
	import_2:
	fmtdisk_0:
	import_3:
	grainsize_3: 8|32|64|128|256.
	compressed:
	filesystem:
	owner: vvol|host_integration_metadata.
	copies:
	filesystem_0:
	udid:
	filesystem_1:
	vtype: seq|striped|image.
	filesystem_2:
	syncrate:
	filesystem_3:
	createsync_0:
	filesystem_4:

Notes:
	None or only one of grainsize,import can appear.
	None or only one of fmtdisk,nofmtdisk,grainsize_0,import_0 can appear.
	None or only one of nofmtdisk_0,grainsize_1,import_1,createsync can appear.
	None or only one of uuid,instance,instance840,grainsize_2,import_2 can appear.
	None or only one of fmtdisk_0,import_3 can appear.
	None or only one of grainsize_3,compressed can appear.
	None or only one of filesystem,owner can appear.
	None or only one of copies,filesystem_0 can appear.
	None or only one of udid,filesystem_1 can appear.
	None or only one of vtype,filesystem_2 can appear.
	None or only one of syncrate,filesystem_3 can appear.
	None or only one of createsync_0,filesystem_4 can appear.'''
        self.assertEqual(expect_, self.conn.svctask.mkvdisk.__doc__)


class Testclispec(TestCase, TestUtilMixin):

    def test_parse_svc_6_3(self):
        res = ucs.parse(getpath('../tests/response/svc-6.3.xml'))
        self.assertEqual('svc', res.array_type)
        self.assertEqual([('svc', '6.3')], res.array_infos)
        self.assertEqual(['CMMV', 'EFFSG', 'EFFST'], res.errors)
        self.assertEqual(
            sorted(['sainfo', 'satask', 'svcinfo', 'svctask']),
            sorted(dir(res)))
        self.assertEqual(5, len(dir(res.sainfo)))
        self.assertEqual(19, len(dir(res.satask)))
        self.assertEqual(95, len(dir(res.svcinfo)))
        self.assertEqual(138, len(dir(res.svctask)))
        self.assertEqual(ucr.SVCResponse, res.svcinfo.lscluster.resp_helper)
        self.assertEqual(['-filtervalue', '-nohdr', '-bytes', '-delim',
                          'cluster', 'cluster_id', 'cluster_name'],
                         [v.realname for _, v in
                          res.svcinfo.lscluster.params.items()])
        self.assertEqual(ucr.SVCResponse, res.svctask.mkmdiskgrp.resp_helper)

    def test_parse_svc_6_2(self):
        res = ucs.parse(getpath('../tests/response/svc-6.2.xml'))
        self.assertEqual('svc', res.array_type)
        self.assertEqual([('svc', '6.2')], res.array_infos)
        self.assertEqual(['CMMV', 'EFFSG', 'EFFST'], res.errors)
        self.assertEqual(sorted(['sainfo', 'satask', 'svcinfo', 'svctask']),
                         sorted(dir(res)))
        self.assertEqual(5, len(dir(res.sainfo)))
        self.assertEqual(18, len(dir(res.satask)))
        self.assertEqual(87, len(dir(res.svcinfo)))
        self.assertEqual(134, len(dir(res.svctask)))
        self.assertEqual(ucr.SVCResponse, res.svcinfo.lscluster.resp_helper)
        self.assertEqual(['-filtervalue', '-nohdr', '-bytes', '-delim',
                          'cluster', 'cluster_id', 'cluster_name'],
                         [v.realname for _, v in
                          res.svcinfo.lscluster.params.items()])
        self.assertEqual(ucr.SVCResponse, res.svctask.mkmdiskgrp.resp_helper)

    def test_parse_svc_6_1(self):
        res = ucs.parse(getpath('../tests/response/svc-6.1.xml'))
        self.assertEqual('svc', res.array_type)
        self.assertEqual([('svc', '6.1')], res.array_infos)
        self.assertEqual(['CMMV', 'EFFSG', 'EFFST'], res.errors)
        self.assertEqual(sorted(['sainfo', 'satask', 'svcinfo', 'svctask']),
                         sorted(dir(res)))
        self.assertEqual(5, len(dir(res.sainfo)))
        self.assertEqual(18, len(dir(res.satask)))
        self.assertEqual(84, len(dir(res.svcinfo)))
        self.assertEqual(132, len(dir(res.svctask)))
        self.assertEqual(ucr.SVCResponse, res.svcinfo.lscluster.resp_helper)
        self.assertEqual(['-filtervalue', '-nohdr', '-bytes', '-delim',
                          'cluster', 'cluster_id', 'cluster_name'],
                         [v.realname for _, v in
                          res.svcinfo.lscluster.params.items()])
        self.assertEqual(ucr.SVCResponse, res.svctask.mkmdiskgrp.resp_helper)

    def test_parse_svc_5_1(self):
        res = ucs.parse(getpath('../tests/response/svc-5.1.xml'))
        self.assertEqual('svc', res.array_type)
        self.assertEqual([('svc', '5.1')], res.array_infos)
        self.assertEqual(['CMMV', 'EFFSG', 'EFFST'], res.errors)
        self.assertEqual(sorted(['svcservicemodeinfo', 'svcservicemodetask',
                                 'svcinfo', 'svctask']), sorted(dir(res)))
        self.assertEqual(14, len(dir(res.svcservicemodeinfo)))
        self.assertEqual(6, len(dir(res.svcservicemodetask)))
        self.assertEqual(88, len(dir(res.svcinfo)))
        self.assertEqual(122, len(dir(res.svctask)))
        self.assertEqual(ucr.SVCResponse, res.svcinfo.lscluster.resp_helper)
        self.assertEqual(['-filtervalue', '-nohdr', '-bytes', '-delim',
                          'cluster', 'cluster_id', 'cluster_name'],
                         [v.realname for _, v in
                          res.svcinfo.lscluster.params.items()])
        self.assertEqual(ucr.SVCResponse, res.svctask.mkmdiskgrp.resp_helper)

    @mock.patch.object(ucr, 'SVCResponse', FakeResponse('svc'))
    def test_parse_v20(self):
        res = ucs.parse(getpath('../tests/response/clispec-sample-2.0.xml'))
        self.assertEqual('svc', res.array_type)
        self.assertEqual([('svc', '6.3')], res.array_infos)
        self.assertEqual(['CMMV', 'EFFSG', 'EFFST'], res.errors)
        self.assertEqual(sorted(['for_test2', 'for_test3', 'sainfo', 'satask',
                                 'svcinfo', 'svcinfo_0', 'svcinfo_1',
                                 'svctask', 'svctask_0', 'svctask_1']),
                         sorted(dir(res)))

        cmd_lscluster = res.svcinfo.lscluster
        self.assertEqual(['filtervalue', 'nohdr', 'bytes', 'delim',
                           'filtervalue_0', 'cluster_id_or_name'],
                         list(cmd_lscluster.params.keys()))
        self.assertEqual('filtervalue_0', cmd_lscluster.params[
                          'filtervalue_0'].name)
        self.assertEqual(
            '-filtervalue?', cmd_lscluster.params['filtervalue_0'].realname)
        self.assertEqual(False, cmd_lscluster.params[
                          'cluster_id_or_name'].with_name)
        self.assertEqual(True, cmd_lscluster.params[
                          'cluster_id_or_name'].with_value)

        cmd_mkhost = res.svctask.mkhost
        self.assertEqual(['name', 'hbawwpn', 'iscsiname', 'iogrp', 'mask',
                          'force', 'type'], list(cmd_mkhost.params.keys()))
        self.assertEqual(['hbawwpn', 'iscsiname'], [
                          p.name for p in cmd_mkhost.param_choices[0].params])
        self.assertEqual(True, cmd_mkhost.param_choices[0].required)
        self.assertEqual(False, cmd_mkhost.params['iogrp'].required)
        self.assertEqual(True, cmd_mkhost.params['force'].with_name)
        self.assertEqual(False, cmd_mkhost.params['force'].with_value)
        self.assertEqual(['hpux', 'tpgs', 'generic'],
                          cmd_mkhost.params['type'].options)

    def test_parse_v20_cmd(self):
        res = ucs.parse(getpath('../tests/response/clispec-sample-2.0.xml'))

        cmd = res.svcinfo.lscluster
        self.assertEqual(ucs.SVCCommand, type(cmd))
        self.assertTrue(ucr.is_svc_response(cmd.resp_helper))
        expect_ = r'''Help on lscluster(**kwargs): Returns a concise list or a detailed view of a cluster. >>- svcinfo -- -- lscluster -- -->
>--
It is wrapper for CLI "svcinfo lscluster".

Parameters:
	filtervalue:
	nohdr:
	bytes:
	delim:
	filtervalue_0:
	cluster_id_or_name:'''
        self.assertEqual(expect_, cmd.__doc__)

        cmd = res.svctask.mkhost
        self.assertEqual(ucs.SVCCommand, type(cmd))
        self.assertTrue(ucr.is_svc_response(cmd.resp_helper))

        cmd = res.for_test2.cmd1
        self.assertEqual(ucs.CLICommand, type(cmd))
        self.assertEqual(None, cmd.resp_helper)
        self.assertEqual(['optiontype', 'optiontype_0',
                           'force', 'noforce'], list(cmd.params.keys()))
        self.assertEqual('for_test2 cmd1 --optiontype?? o1',
                         cmd(nothing, {'optiontype': 'o1',
                                       'xsf.check_return_code': False}))
        self.assertEqual('for_test2 cmd1 --optiontype tryonce',
                         cmd(nothing, {'optiontype_0': 'tryonce',
                                       'xsf.check_return_code': False}))
        self.assertRaisesEx(ucs.CLISpecError, cmd, nothing,
                            dict(optiontype_0='bad'))

        cmd = res.for_test3
        self.assertEqual(ucs.CLICommand, type(cmd))
        self.assertEqual(None, cmd.resp_helper)
        self.assertEqual(['network', 'interface', 'g',
                           'force'], list(cmd.params.keys()))
        self.assertEqual('for_test3 n1 inf1 -g g1 --force %s' %
                         ucs.show_return_code_if_fail(),
                         cmd(nothing, dict(network='n1', interface='inf1',
                                           g='g1', force=None)))
        self.assertRaisesEx(ucs.CLISpecError, cmd, nothing,
                            dict(interface='inf1', g='g1'))

    @mock.patch.object(ucr, 'SVCResponse', FakeResponse('svc'))
    def test_cmd_input(self):
        res = ucs.parse(getpath('../tests/response/svc-6.3.xml'))
        cmd = res.svcinfo.lsnode
        self.assertEqual(ucs.SVCCommand, type(cmd))
        self.assertTrue(ucr.is_svc_response(cmd.resp_helper))
        self.assertEqual('svcinfo lsnode -delim , 1 %s' %
                          ucs.show_return_code_if_fail(),
                         cmd(nothing, dict(object='1')))
        self.assertEqual('svcinfo lsnode -delim , 1 %s' %
                         ucs.show_return_code_if_fail(),
                         cmd(nothing, {'object': '1', 'xsf.ignore': '1'}))
        self.assertEqual('svcinfo lsnode -delim , 1 %s' %
                         ucs.show_return_code_if_fail(),
                         cmd(nothing, {'object': '1', 'badparam': '1',
                                       'xsf.flexible': True}))
        self.assertRaisesEx(ucs.CLISpecError, cmd, nothing,
                            dict(object='1', badparam='1'))

    def test_parse_bad_xml_pi(self):
        self.assertRaisesEx(ucs.CLISpecError, ucs.parse,
                            StringIO(SPEC_BAD_XML_PI))

    def test_parse_no_version(self):
        self.assertRaisesEx(ucs.CLISpecError, ucs.parse,
                            StringIO(SPEC_NO_VERSION))
        expect_ = ucs.parse(StringIO(SPEC_NO_VERSION), flexible=True)
        self.assertTrue(expect_.cmds)

    def test_parse_no_array_type(self):
        self.assertRaisesEx(ucs.CLISpecError, ucs.parse,
                            StringIO(SPEC_NO_ARRAY_TYPE))
        expect_ = ucs.parse(StringIO(SPEC_NO_ARRAY_TYPE), flexible=True)
        self.assertTrue(expect_.cmds)

    def test_parse_no_error(self):
        res = ucs.parse(StringIO(SPEC_NO_ERROR))
        self.assertEqual([''], res.errors)

    def test_parse_no_exe_name(self):
        self.assertRaisesEx(ucs.CLISpecError, ucs.parse,
                            StringIO(SPEC_NO_EXE_NAME))
        expect_ = ucs.parse(StringIO(SPEC_NO_EXE_NAME), flexible=True)
        self.assertFalse(expect_.cmds)

    def test_parse_empty_exe_name(self):
        self.assertRaisesEx(ucs.CLISpecError, ucs.parse,
                            StringIO(SPEC_EMPTY_EXE_NAME))
        expect_ = ucs.parse(StringIO(SPEC_EMPTY_EXE_NAME), flexible=True)
        self.assertFalse(expect_.cmds)

    def test_parse_no_cmd(self):
        conn = uc.UnifiedSSHClient()
        conn.flexible = True
        res = uc.parse_cli_spec(conn, StringIO(SPEC_EMPTY_EXE_NAME))
        self.assertFalse(res)

    def test_parse_no_cmd_name(self):
        self.assertRaisesEx(ucs.CLISpecError, ucs.parse,
                            StringIO(SPEC_NO_CMD_NAME))
        expect_ = ucs.parse(StringIO(SPEC_NO_CMD_NAME), flexible=True)
        self.assertTrue(expect_.cmds['svcinfo'].cmds['lscluster'])

    def test_parse_empty_cmd_name(self):
        self.assertRaisesEx(ucs.CLISpecError, ucs.parse,
                            StringIO(SPEC_EMPTY_CMD_NAME))
        expect_ = ucs.parse(StringIO(SPEC_EMPTY_CMD_NAME), flexible=True)
        self.assertFalse(expect_.cmds['svcinfo'].cmds)

    def test_parse_no_param_name(self):
        self.assertRaisesEx(ucs.CLISpecError, ucs.parse,
                            StringIO(SPEC_NO_PARAM_NAME))
        expect_ = ucs.parse(StringIO(SPEC_NO_PARAM_NAME), flexible=True)
        self.assertEqual(
            5, len(expect_.cmds['svcinfo'].cmds['lscluster'].params))

    def test_parse_empty_param_name(self):
        self.assertRaisesEx(ucs.CLISpecError, ucs.parse,
                            StringIO(SPEC_EMPTY_PARAM_NAME))
        expect_ = ucs.parse(StringIO(SPEC_EMPTY_PARAM_NAME), flexible=True)
        self.assertEqual(
            5, len(expect_.cmds['svcinfo'].cmds['lscluster'].params))
        self.assertEqual(0, len(expect_.cmds['svcinfo'].cmds[
                          'lscluster'].param_choices))

    def test_compress_extract_str(self):
        instr = SPEC_COMMANDS_SVC_SIMPLE.encode()
        outstr = ucs.compress_str(instr)
        self.assertEqual(instr, ucs.extract_str(outstr.decode()))


class TestMisc(TestCase):

    def test_get_cli_spec(self):
        self.assertTrue(uc.get_cli_spec('tests/response/clispec-sample', '2.0'))
        self.assertTrue(uc.get_cli_spec('tests/response/xsf', '1.0'))
        self.assertTrue(uc.get_cli_spec('tests/response/svc', '5.1'))
        self.assertTrue(uc.get_cli_spec('tests/response/svc', '6.1'))
        self.assertTrue(uc.get_cli_spec('tests/response/svc', '6.2'))
        self.assertTrue(uc.get_cli_spec('tests/response/svc', '6.3'))

        self.assertRaises(IOError, uc.get_cli_spec, 'xsf', '2.0')
        self.assertRaises(IOError, uc.get_cli_spec, 'svc', '4.3')
        self.assertRaises(IOError, uc.get_cli_spec, 'svc', '5.2')
        self.assertRaises(IOError, uc.get_cli_spec, 'svc', '7.1')

    def test_escape_shell_arg(self):
        self.assertEqual('a12bZ', ucs.escape_shell_arg('a12bZ'))
        self.assertEqual("'a12 bZ'", ucs.escape_shell_arg('a12 bZ'))
        self.assertEqual("'a12 \t \n bZ'",
                          ucs.escape_shell_arg('a12 \t \n bZ'))
        self.assertEqual("'\"a12bZ\"'", ucs.escape_shell_arg('"a12bZ"'))
        self.assertEqual("'a12 && bZ'", ucs.escape_shell_arg('a12 && bZ'))
        self.assertEqual("'a12 || bZ'", ucs.escape_shell_arg('a12 || bZ'))
        self.assertEqual("'a12\"bZ'", ucs.escape_shell_arg('a12\"bZ'))
        self.assertEqual('', ucs.escape_shell_arg(''))
        self.assertEqual("' '", ucs.escape_shell_arg(' '))
        self.assertEqual("'a-b'", ucs.escape_shell_arg('a-b'))
        self.assertEqual("'a_b'", ucs.escape_shell_arg('a_b'))

    def test_sniffer(self):
        snif = ucr.MySniffer(',')
        self.assertFalse(snif.has_header(''))


class TestSVCResponse(TestCase, TestUtilMixin):

    @mock.patch.object(MySniffer, 'has_header',
                       mock.Mock(side_effect=RuntimeError(
                           'MySniffer.has_header() should not be called.')))
    def test_with_header(self):
        helper = ucr.find_response_helper('svc_detailed')
        res = helper(RESP_svcinfo_lscurrentuser,
                     dict(delim=',', with_header=True))
        self.assertEqual(1, len(res.as_list))
        self.assertEqual([('name', 'role'), ('superuser', 'SecurityAdmin')],
                         sorted(res.as_list[0].items()))

        res = helper(RESP_svcinfo_lscurrentuser,
                     dict(delim=',', with_header=False))
        self.assertEqual(1, len(res.as_list))
        self.assertEqual([('name', 'superuser'), ('role', 'SecurityAdmin')],
                         sorted(res.as_list[0].items()))

    def test_with_header_empty_input(self):
        helper = ucr.find_response_helper('svc_detailed')
        res = helper('   ', dict(delim=',', with_header=True))
        self.assertEqual(0, len(res.as_list))

        helper = ucr.find_response_helper('svc_detailed')
        res = helper('', dict(delim=',', with_header=True))
        self.assertEqual(0, len(res.as_list))

    def test_svcinfo_nothing(self):
        helper = ucr.find_response_helper('svc')
        res = helper(RESP_svcinfo_nothing)
        self.assertEqual(0, len(res.as_list))

    def test_svcinfo_lscluster(self):
        helper = ucr.find_response_helper('svc_normal')

        res = helper(RESP_svcinfo_lscluster, dict(delim=','))
        self.assertEqual(2, len(res.as_list))
        expect_ = [('bandwidth', ''), ('id', '000002006700D9FC'),
                   ('id_alias', '000002006700D9FC'), ('location', 'local'),
                   ('name', 'CIMV7000'), ('partnership', '')]
        self.assertEqual(expect_, sorted(res.as_list[0].items()))
        self.assertEqual(expect_, sorted(
            res.as_dict('id')['000002006700D9FC'].items()))

        expect_ = [('bandwidth', '20'), ('id', '000002006500C4FC'),
                   ('id_alias', '000002006500C4FC'), ('location', 'remote'),
                   ('name', 'CIMFVTV7000'),
                   ('partnership', 'fully_configured')]
        self.assertEqual(expect_, sorted(res.as_list[1].items()))
        self.assertEqual(expect_, sorted(
            res.as_dict('id')['000002006500C4FC'].items()))

    def test_svcinfo_lscluster_id(self):
        helper = ucr.find_response_helper('svc_normal')
        res = helper(RESP_svcinfo_lscluster_id, dict(delim=','))
        self.assertEqual(1, len(res.as_list))
        expect_ = [('FC_port_speed', '2Gb'), ('auth_service_cert_set', 'no'),
                   ('auth_service_configured', 'no'),
                   ('auth_service_enabled', 'no'),
                   ('auth_service_pwd_set', 'no'),
                   ('auth_service_type', 'tip'), ('auth_service_url', ''),
                   ('auth_service_user_name', ''), ('bandwidth', ''),
                   ('cluster_isns_IP_address', ''),
                   ('cluster_locale', 'en_US'),
                   ('cluster_ntp_IP_address', ''),
                   ('code_level', '6.3.0.0 (build 52.5.1106290000)'),
                   ('console_IP', '9.119.41.132:443'), ('email_contact', ''),
                   ('email_contact2', ''), ('email_contact2_alternate', ''),
                   ('email_contact2_primary', ''),
                   ('email_contact_alternate', ''),
                   ('email_contact_location', ''),
                   ('email_contact_primary', ''), ('email_reply', ''),
                   ('email_state', 'stopped'),
                   ('gm_inter_cluster_delay_simulation', '0'),
                   ('gm_intra_cluster_delay_simulation', '0'),
                   ('gm_link_tolerance', '300'), ('gm_max_host_delay', '5'),
                   ('has_nas_key', 'no'), ('id', '000002006700D9FC'),
                   ('id_alias', '000002006700D9FC'),
                   ('inventory_mail_interval', '0'),
                   ('iscsi_auth_method', 'none'), ('iscsi_chap_secret', ''),
                   ('layer', 'controller'), ('location', 'local'),
                   ('name', 'CIMV7000'), ('partnership', ''),
                   ('relationship_bandwidth_limit', '25'),
                   ('required_memory', '0'),
                   ('space_allocated_to_vdisks', '246.81GB'),
                   ('space_in_mdisk_grps', '2.2TB'),
                   ('statistics_frequency', '15'),
                   ('statistics_status', 'on'),
                   ('tier', ['generic_ssd', 'generic_hdd']),
                   ('tier_capacity', ['0.00MB', '2.20TB']),
                   ('tier_free_capacity', ['0.00MB', '1.95TB']),
                   ('time_zone', '522 UTC'),
                   ('total_allocated_extent_capacity', '247.03GB'),
                   ('total_free_space', '2.0TB'),
                   ('total_mdisk_capacity', '2.3TB'),
                   ('total_overallocation', '10'),
                   ('total_used_capacity', '241.68GB'),
                   ('total_vdisk_capacity', '251.62GB'),
                   ('total_vdiskcopy_capacity', '251.62GB')]
        self.assertEqual(expect_, sorted(res.as_list[0].items()))
        self.assertEqual(expect_, sorted(res.as_dict('code_level')[
                          '6.3.0.0 (build 52.5.1106290000)'].items()))
        self.assertEqual(['generic_ssd', 'generic_hdd'],
                          res.as_dict('id')['000002006700D9FC']['tier'])

    def test_svcinfo_lsvdisk(self):
        helper = ucr.find_response_helper('svc_normal')
        res = helper(RESP_svcinfo_lsvdisk, dict(delim=','))
        self.assertEqual(4, len(res.as_list))
        self.assertEqual('0', res.as_list[0].id)
        self.assertEqual('io_grp0', res.as_list[0].IO_group_name)
        self.assertEqual('2', res.as_list[2].id)
        self.assertEqual('40.00GB', res.as_list[2].capacity)
        self.assertEqual('', res.as_list[2].FC_name)
        self.assertEqual('3', res.as_list[3].id)
        self.assertEqual('forvcplugintest', res.as_list[3].mdisk_grp_name)

        self.assertEqual('offline', res.as_dict('id')['1'].status)
        self.assertEqual('striped', res.as_dict('id')['1'].type)
        self.assertEqual('empty', res.as_dict('id')['1'].fast_write_state)

    def test_svcinfo_lsvdisk_id(self):
        helper = ucr.find_response_helper('svc_normal')
        res = helper(RESP_svcinfo_lsvdisk_id, dict(delim=','))
        self.assertEqual(2, len(res.as_list))

        one_ = res.as_single_element
        expect_ = [('FC_id', '0'), ('FC_name', 'fcmap0'),
                   ('IO_group_id', '0'), ('IO_group_name', 'io_grp0'),
                   ('RC_id', '0'), ('RC_name', 'rcrel8'), ('autoexpand', ''),
                   ('cache', 'readwrite'), ('capacity', '100.00MB'),
                   ('compressed_copy', 'no'), ('compressed_copy_count', '0'),
                   ('copy_count', '1'), ('copy_id', '0'), ('easy_tier', 'on'),
                   ('easy_tier_status', 'inactive'),
                   ('fast_write_state', 'empty'), ('fc_map_count', '1'),
                   ('filesystem', ''), ('formatted', 'no'),
                   ('free_capacity', '0.00MB'), ('grainsize', ''),
                   ('id', '0'), ('mdisk_grp_id', '5'),
                   ('mdisk_grp_name', 'mdiskgrp2'), ('mdisk_id', ''),
                   ('mdisk_name', ''), ('name', 'vdisk0'),
                   ('overallocation', '100'), ('preferred_node_id', '2'),
                   ('primary', 'yes'), ('real_capacity', '100.00MB'),
                   ('se_copy', 'no'), ('se_copy_count', '0'),
                   ('status', 'online'), ('sync', 'yes'), ('sync_rate', '50'),
                   ('throttling', '0'),
                   ('tier', ['generic_ssd', 'generic_hdd']),
                   ('tier_capacity', ['0.00MB', '100.00MB']),
                   ('type', 'striped'), ('udid', ''),
                   ('used_capacity', '100.00MB'),
                   ('vdisk_UID', '60050768019C0367F000000000000023'),
                   ('warning', '')]
        # self.assertEquals(len(expect_), len(sorted(res.as_list[0].items())))
        self.assertEqual(len(expect_), len(one_))
        self.assertEqual(expect_, sorted(one_.items()))
        self.assertEqual('0', one_.id)
        self.assertEqual('5', one_.mdisk_grp_id)
        self.assertEqual('mdiskgrp2', one_.mdisk_grp_name)
        self.assertEqual(['generic_ssd', 'generic_hdd'], one_.tier)

        self.assertEqual('0', res.as_list[0].id)
        self.assertEqual('0', res.as_list[1].copy_id)

    def test_svcinfo_lssevdiskcopy(self):
        helper = ucr.find_response_helper('svc_concise', param='copy')
        res = helper(RESP_svcinfo_lssevdiskcopy, dict(delim=','))
        self.assertEqual(11, len(res.as_list))
        expect_ = [('autoexpand', 'on'), ('capacity', '1.00GB'),
                   ('compressed_copy', 'no'), ('copy_id', '0'),
                   ('free_capacity', '527.97MB'), ('grainsize', '32'),
                   ('mdisk_grp_id', '0'), ('mdisk_grp_name', 'waynestudy720'),
                   ('overallocation', '193'), ('real_capacity', '528.38MB'),
                   ('se_copy', 'yes'), ('used_capacity', '0.41MB'),
                   ('vdisk_id', '13'), ('vdisk_name', 'wayneTest12'),
                   ('warning', '0')]
        self.assertEqual(len(expect_), len(sorted(res.as_list[0].items())))
        self.assertEqual(expect_, sorted(res.as_list[0].items()))
        self.assertEqual('13', res.as_list[0].vdisk_id)
        self.assertEqual('no', res.as_list[0].compressed_copy)

    def test_svcinfo_lssevdiskcopy_id(self):
        helper = ucr.find_response_helper('svc_concise', param='copy')
        res = helper(RESP_svcinfo_lssevdiskcopy_id, dict(delim=','))
        self.assertEqual(1, len(res.as_list))
        expect_ = [('autoexpand', 'on'), ('capacity', '1.00GB'),
                   ('compressed_copy', 'no'), ('copy_id', '0'),
                   ('free_capacity', '527.97MB'), ('grainsize', '32'),
                   ('mdisk_grp_id', '0'), ('mdisk_grp_name', 'waynestudy720'),
                   ('overallocation', '193'), ('real_capacity', '528.38MB'),
                   ('se_copy', 'yes'), ('used_capacity', '0.41MB'),
                   ('vdisk_id', '15'), ('vdisk_name', 'vdisk3'),
                   ('warning', '80')]
        self.assertEqual(len(expect_), len(sorted(res.as_list[0].items())))
        self.assertEqual(expect_, sorted(res.as_list[0].items()))
        self.assertEqual('15', res.as_list[0].vdisk_id)
        self.assertEqual('no', res.as_list[0].compressed_copy)
        self.assertEqual('32', res.as_list[0].grainsize)

    def test_svcinfo_lssevdiskcopy_id_copy(self):
        helper = ucr.find_response_helper('svc_concise', param='copy')
        res = helper(RESP_svcinfo_lssevdiskcopy_id_copy, dict(delim=','))
        self.assertEqual(1, len(res.as_list))
        expect_ = [('autoexpand', 'on'), ('capacity', '1.00GB'),
                   ('compressed_copy', 'no'), ('copy_id', '0'),
                   ('easy_tier', 'on'), ('easy_tier_status', 'inactive'),
                   ('fast_write_state', 'empty'),
                   ('free_capacity', '527.97MB'), ('grainsize', '32'),
                   ('mdisk_grp_id', '0'),
                   ('mdisk_grp_name', 'waynestudy720'), ('mdisk_id', ''),
                   ('mdisk_name', ''), ('overallocation', '193'),
                   ('primary', 'yes'), ('real_capacity', '528.38MB'),
                   ('se_copy', 'yes'), ('status', 'online'), ('sync', 'yes'),
                   ('tier', ['generic_ssd', 'generic_hdd']),
                   ('tier_capacity', ['0.00MB', '528.38MB']),
                   ('type', 'striped'), ('used_capacity', '0.41MB'),
                   ('vdisk_id', '15'), ('vdisk_name', 'vdisk3'),
                   ('warning', '80')]
        self.assertEqual(len(expect_), len(sorted(res.as_list[0].items())))
        self.assertEqual(expect_, sorted(res.as_list[0].items()))
        self.assertEqual('15', res.as_list[0].vdisk_id)
        self.assertEqual('no', res.as_list[0].compressed_copy)
        self.assertEqual(['0.00MB', '528.38MB'], res.as_list[0].tier_capacity)

    def test_svcinfo_lsclusterip(self):
        helper = ucr.find_response_helper('svc_grouped_detail_or_concise')
        res = helper(RESP_svcinfo_lsclusterip, dict(delim=','))
        self.assertEqual(4, len(res.as_list))
        expect_ = [('IP_address', '9.119.41.132'), ('IP_address_6', ''),
                   ('cluster_id', '000002006700D9FC'),
                   ('cluster_name', 'CIMV7000'),
                   ('gateway', '9.119.41.1'), ('gateway_6', ''),
                   ('location', 'local'), ('port_id', '1'), ('prefix_6', ''),
                   ('subnet_mask', '255.255.255.0')]
        self.assertEqual(expect_, sorted(res.as_list[0].items()))

        res = helper(RESP_svcinfo_lsclusterip_id, dict(delim=','))
        self.assertEqual(2, len(res.as_list))
        expect_ = [('IP_address', '9.119.41.132'), ('IP_address_6', ''),
                   ('cluster_id', '000002006700D9FC'),
                   ('cluster_name', 'CIMV7000'),
                   ('gateway', '9.119.41.1'), ('gateway_6', ''),
                   ('location', 'local'), ('port_id', '1'), ('prefix_6', ''),
                   ('subnet_mask', '255.255.255.0')]
        self.assertEqual(expect_, sorted(res.as_list[0].items()))
        expect_ = [('IP_address', ''), ('IP_address_6', ''),
                   ('cluster_id', '000002006700D9FC'),
                   ('cluster_name', 'CIMV7000'),
                   ('gateway', ''), ('gateway_6', ''),
                   ('location', 'local'), ('port_id', '2'), ('prefix_6', ''),
                   ('subnet_mask', '')]
        self.assertEqual(expect_, sorted(res.as_list[1].items()))

    def test_svcinfo_lsnodevpd_id(self):
        helper = ucr.find_response_helper('svc_nested_fields')
        res = helper(RESP_svcinfo_lsnodevpd_id, dict(delim=','))
        self.assertEqual(22, len(res.as_list))
        self.assertEqual(sorted([('id', '1')]),
                          sorted(res.as_list[0].items()))
        self.assertEqual('', res.as_list[1]['system board: 23 fields'])
        self.assertEqual('85Y5899', res.as_list[1].part_number)
        self.assertEqual('Processor 1', res.as_list[2].processor_location)
        self.assertEqual('e4:1f:13:74:06:1e', res.as_list[-1].MAC_address)
        self.assertEqual('RCK0949138G004D',
                          res.as_single_element.system_serial_number)
        self.assertEqual(sorted([('id', '1')]),
                          sorted(res.as_list[0].items()))

    def test_svcinfo_lsroute(self):
        helper = ucr.find_response_helper('svc_custom', 'lsroute')
        res = helper(RESP_svcinfo_lsroute)
        self.assertEqual(7, len(res.as_list))
        expect_ = [('Destination', '9.119.41.0'), ('Flags', 'U'),
                   ('Gateway', '0.0.0.0'), ('Genmask', '255.255.255.0'),
                   ('Iface', 'eth0'), ('Metric', '0'), ('Ref', '0'),
                   ('Use', '0')]
        self.assertEqual(expect_, sorted(res.as_list[0].items()))
        expect_ = [('Destination', 'ff00::/8'), ('Flags', 'U'),
                   ('Iface', 'eth0'),  ('Metric', '256'), ('Next_Hop', '::'),
                   ('Ref', '0'), ('Use', '0')]
        self.assertEqual(expect_, sorted(res.as_list[6].items()))

    def test_svcinfo_lscurrentuser(self):
        helper = ucr.find_response_helper('svc_detailed')
        res = helper(RESP_svcinfo_lscurrentuser, dict(delim=','))
        self.assertEqual(1, len(res.as_list))
        self.assertEqual([('name', 'superuser'), ('role', 'SecurityAdmin')],
                         sorted(res.as_list[0].items()))

    def test_svcinfo_lssoftwareupgradestatus(self):
        helper = ucr.find_response_helper('svc_detailed')
        res = helper(RESP_svcinfo_lssoftwareupgradestatus)
        self.assertEqual(1, len(res.as_list))
        self.assertEqual([('status', 'inactive')],
                          sorted(res.as_list[0].items()))

    def test_svcinfo_lshbaportcandidate(self):
        helper = ucr.find_response_helper('svc_concise')
        res = helper(RESP_svcinfo_lshbaportcandidate, dict(delim=','))
        self.assertEqual(3, len(list(res)))
        self.assertEqual([('id', '50050768014043E4')],
                          sorted(list(res)[0].items()))
        self.assertEqual([('id', '5005076802301806')],
                          sorted(list(res)[1].items()))
        self.assertEqual([('id', '500507680140436C')],
                          sorted(list(res)[2].items()))

    def test_lsmdiskgrp(self):
        helper = ucr.find_response_helper('svc_normal')

    def test_lsiogrp(self):
        helper = ucr.find_response_helper('svc_normal')

    def test_lsfcmap(self):
        helper = ucr.find_response_helper('svc_normal')

    def test_lsrcrelationship(self):
        helper = ucr.find_response_helper('svc_normal')

    def test_lshost(self):
        helper = ucr.find_response_helper('svc_normal')

    def test_svctask_mkvdisk(self):
        helper = ucr.find_response_helper('svc_status')
        res = helper(RESP_svctask_mkvdisk)
        self.assertEqual(0, len(res.as_list))

    def test_svctask_mkvdisk_err(self):
        helper = ucr.find_response_helper('svc_status')
        try:
            helper(('I have error.\n%s 4 xy -5 xy 6\n' % ucs.TAG_ERR,
                    RESP_svctask_mkvdisk_err), dict(error_tag=ucs.TAG_ERR))
        except ucr.CLIFailureError as ex:
            expect_ = r'CLI failure. Return code is 4 -5 6. Error message ' \
                      r'is "CMMVC6432E The command failed because the ' \
                      r'specified managed disk group does not exist."'
            self.assertEqual(expect_, ex.my_message)
            return
        self.assertTrue(False, 'No exception raised.')


if __name__ == '__main__':
    unittest.main()
