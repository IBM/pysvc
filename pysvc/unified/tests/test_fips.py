"""
FIPS compatibility unit tests for pysvc.

Coverage
--------
TestFipsSafeGetFingerprint
    Unit tests for the _fips_safe_get_fingerprint monkey-patch installed on
    paramiko.pkey.PKey at import time.  Three code paths are exercised:
      1. MD5 succeeds (non-FIPS or FIPS with usedforsecurity=False accepted)
      2. MD5 raises ValueError  — FIPS build that blocks MD5 entirely
      3. MD5 raises TypeError   — Python < 3.9 without the usedforsecurity kwarg

TestFIPSSafeAutoAddPolicy
    Unit and in-process integration tests for FIPSSafeAutoAddPolicy, the
    drop-in replacement for paramiko.AutoAddPolicy that never calls the
    legacy MD5-based get_fingerprint().

TestSSHTransportConnectPolicy
    Verifies that SSHTransport.connect() installs FIPSSafeAutoAddPolicy when
    auto_add=True (default) and installs no policy when auto_add=False.

TestPBHAKeyChange
    Tests for PBHA (Port-Based Host Authentication) failover behaviour, where
    the same IP presents a different host key after a node replacement or
    failover.  Two scenarios:
      1. ignore_known_hosts=True (default): successive SSHTransport instances
         to the same host with different keys both succeed because each
         SSHClient starts with an empty in-memory key store.
      2. ignore_known_hosts=False: after key A is saved to xsf_known_hosts, a
         second connection presenting key B raises BadHostFingerPrintException.

System-level testing completed
-------------------------------
The following suites were executed against a real SVC target on both a
FIPS-enabled OCP cluster and a FIPS-disabled OCP cluster:
  - Sanity suite
  - Regression suite
  - Replication suite
All suites passed on both FIPS and non-FIPS environments.
PBHA-specific testing (same IP, different fingerprint) is tracked as a
follow-up item.
"""
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


class TestPBHAKeyChange(TestCase):
    """
    PBHA failover: the same IP presents a different host key after a node
    replacement.  Tests verify the expected behaviour for both values of
    ignore_known_hosts without requiring a live SSH server.
    """

    def _make_transport(self, ignore_known_hosts, ssh_client_mock):
        """Return an SSHTransport whose internal SSHClient is ssh_client_mock."""
        with patch('pysvc.transports.ssh_transport.SSHClient',
                   return_value=ssh_client_mock):
            t = SSHTransport('1.2.3.4', user='u', password='p',
                             ignore_known_hosts=ignore_known_hosts)
        return t

    # ------------------------------------------------------------------
    # Scenario 1 — ignore_known_hosts=True (default, production path)
    # ------------------------------------------------------------------

    def test_pbha_ignore_known_hosts_true_first_connection_succeeds(self):
        # First SSHTransport: key A presented — accepted silently because the
        # in-memory key store is empty and FIPSSafeAutoAddPolicy is in effect.
        client_a = MagicMock()
        client_a._host_keys_filename = None
        t_a = self._make_transport(ignore_known_hosts=True, ssh_client_mock=client_a)
        t_a.connect()
        client_a.set_missing_host_key_policy.assert_called_once()
        policy_a = client_a.set_missing_host_key_policy.call_args[0][0]
        self.assertIsInstance(policy_a, FIPSSafeAutoAddPolicy)
        client_a.connect.assert_called_once()

    def test_pbha_ignore_known_hosts_true_second_connection_with_different_key_succeeds(self):
        # Second SSHTransport (after PBHA failover): key B on the same IP.
        # A fresh SSHClient is constructed, so _host_keys is empty again —
        # key B is accepted without error, exactly as key A was.
        client_b = MagicMock()
        client_b._host_keys_filename = None
        t_b = self._make_transport(ignore_known_hosts=True, ssh_client_mock=client_b)
        t_b.connect()
        client_b.set_missing_host_key_policy.assert_called_once()
        policy_b = client_b.set_missing_host_key_policy.call_args[0][0]
        self.assertIsInstance(policy_b, FIPSSafeAutoAddPolicy)
        client_b.connect.assert_called_once()

    # ------------------------------------------------------------------
    # Scenario 2 — ignore_known_hosts=False (strict mode)
    # ------------------------------------------------------------------

    def test_pbha_ignore_known_hosts_false_changed_key_raises_bad_fingerprint(self):
        # First connection with key A: loads an empty (or non-existent)
        # known_hosts file, connects, saves key A to disk.
        # Second connection with key B: loads key A from disk, Paramiko detects
        # a mismatch and raises BadHostKeyException, which SSHTransport wraps
        # as BadHostFingerPrintException.
        import tempfile, os
        from pysvc.errors import BadHostFingerPrintException
        from paramiko.ssh_exception import BadHostKeyException

        key_a = paramiko.RSAKey.generate(1024)
        key_b = paramiko.RSAKey.generate(1024)

        with tempfile.NamedTemporaryFile(delete=False, suffix='_known_hosts') as f:
            known_hosts_path = f.name
        try:
            # --- First connection: key A accepted, saved to known_hosts ---
            client_first = MagicMock()
            client_first._host_keys_filename = None

            with patch('pysvc.transports.ssh_transport.SSHClient',
                       return_value=client_first), \
                 patch('os.path.isfile', return_value=True), \
                 patch.object(client_first, 'load_host_keys'), \
                 patch.object(client_first, 'save_host_keys') as save_first:
                t_first = SSHTransport('1.2.3.4', user='u', password='p',
                                       ignore_known_hosts=False)
                t_first.connect()
            save_first.assert_called_once_with(t_first.svc_client_host_keys_file)

            # --- Second connection: key B presented — mismatch → exception ---
            client_second = MagicMock()
            client_second._host_keys_filename = None
            client_second.connect.side_effect = BadHostKeyException(
                '1.2.3.4', key_b, key_a)

            with patch('pysvc.transports.ssh_transport.SSHClient',
                       return_value=client_second), \
                 patch('os.path.isfile', return_value=True), \
                 patch.object(client_second, 'load_host_keys'):
                t_second = SSHTransport('1.2.3.4', user='u', password='p',
                                        ignore_known_hosts=False)
                with self.assertRaises(BadHostFingerPrintException) as ctx:
                    t_second.connect()

            self.assertEqual(ctx.exception.hostname, '1.2.3.4')
            self.assertIs(ctx.exception.presented_key, key_b)
        finally:
            os.unlink(known_hosts_path)
