import hashlib
from unittest import TestCase
from unittest.mock import patch, MagicMock

import paramiko

import pysvc
from pysvc.transports import ssh_transport
from pysvc.transports.ssh_transport import FIPSSafeAutoAddPolicy, SSHTransport

KEY_BYTES = b'fake-public-key-bytes'


class TestFipsSafeGetFingerprint(TestCase):

    def setUp(self):
        self.key = MagicMock()
        self.key.asbytes.return_value = KEY_BYTES

    def test_patch_is_installed_on_paramiko(self):
        self.assertIs(paramiko.pkey.PKey.get_fingerprint,
                      pysvc._fips_safe_get_fingerprint)

    def test_returns_md5_when_allowed(self):
        result = pysvc._fips_safe_get_fingerprint(self.key)
        self.assertEqual(
            result, hashlib.md5(KEY_BYTES, usedforsecurity=False).digest())

    def test_md5_called_with_usedforsecurity_false(self):
        with patch.object(pysvc.hashlib, 'md5') as md5:
            pysvc._fips_safe_get_fingerprint(self.key)
        md5.assert_called_once_with(KEY_BYTES, usedforsecurity=False)

    def _assert_sha256_fallback(self, error):
        with patch.object(pysvc.hashlib, 'md5', side_effect=error):
            result = pysvc._fips_safe_get_fingerprint(self.key)
        self.assertEqual(result, hashlib.sha256(KEY_BYTES).digest()[:16])
        self.assertEqual(len(result), 16)

    def test_fallback_to_sha256_when_md5_blocked_by_fips(self):
        self._assert_sha256_fallback(
            ValueError('[digital envelope routines] unsupported'))

    def test_fallback_to_sha256_when_usedforsecurity_unsupported(self):
        self._assert_sha256_fallback(TypeError('unexpected keyword'))

    def test_real_key_get_fingerprint_works(self):
        key = paramiko.RSAKey.generate(2048)
        self.assertEqual(len(key.get_fingerprint()), 16)


class TestFIPSSafeAutoAddPolicy(TestCase):

    def setUp(self):
        self.policy = FIPSSafeAutoAddPolicy()
        self.client = MagicMock()
        self.client._host_keys_filename = None
        self.key = MagicMock()
        self.key.get_name.return_value = 'ssh-rsa'
        self.key.asbytes.return_value = KEY_BYTES

    def test_adds_host_key(self):
        self.policy.missing_host_key(self.client, 'svc-host', self.key)
        self.client._host_keys.add.assert_called_once_with(
            'svc-host', 'ssh-rsa', self.key)

    def test_does_not_call_md5_get_fingerprint(self):
        self.policy.missing_host_key(self.client, 'svc-host', self.key)
        self.key.get_fingerprint.assert_not_called()

    def test_saves_host_keys_when_filename_set(self):
        self.client._host_keys_filename = '/tmp/known_hosts'
        self.policy.missing_host_key(self.client, 'svc-host', self.key)
        self.client.save_host_keys.assert_called_once_with('/tmp/known_hosts')

    def test_does_not_save_host_keys_when_no_filename(self):
        self.policy.missing_host_key(self.client, 'svc-host', self.key)
        self.client.save_host_keys.assert_not_called()

    def test_logs_sha256_fingerprint(self):
        with patch.object(ssh_transport.xlog, 'debug') as debug:
            self.policy.missing_host_key(self.client, 'svc-host', self.key)
        debug.assert_called_once_with(
            "Added %s host key for %s (SHA256: %s)", 'ssh-rsa', 'svc-host',
            hashlib.sha256(KEY_BYTES).hexdigest())

    def test_logging_error_does_not_fail(self):
        self.key.asbytes.side_effect = Exception('boom')
        self.policy.missing_host_key(self.client, 'svc-host', self.key)
        self.client._host_keys.add.assert_called_once()

    def test_with_real_ssh_client_and_key(self):
        client = paramiko.SSHClient()
        key = paramiko.RSAKey.generate(2048)
        self.policy.missing_host_key(client, 'svc-host', key)
        self.assertEqual(client.get_host_keys().lookup('svc-host')['ssh-rsa'],
                         key)


@patch('pysvc.transports.ssh_transport.SSHClient')
class TestSSHTransportConnectPolicy(TestCase):

    def test_connect_uses_fips_safe_policy(self, ssh_client):
        SSHTransport('svc-host', user='u', password='p').connect()
        policy = ssh_client.return_value.set_missing_host_key_policy \
            .call_args[0][0]
        self.assertIsInstance(policy, FIPSSafeAutoAddPolicy)

    def test_connect_without_auto_add_sets_no_policy(self, ssh_client):
        SSHTransport('svc-host', user='u', password='p',
                     auto_add=False).connect()
        ssh_client.return_value.set_missing_host_key_policy.assert_not_called()
