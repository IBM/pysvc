from unittest import TestCase
from mock import patch, Mock
from container.storage_agent_service.util.ssh_utils import SSHPool


class TestSshUtils(TestCase):

    def setUp(self):
        connect_patcher = patch('container.storage_agent_service.util.ssh_utils.connect')
        self.connect_mock = connect_patcher.start()
        self.addCleanup(connect_patcher.stop)

    def test_get_same_client(self):
        self.connect_mock.side_effect = [Mock(), Mock()]
        pool = SSHPool("1.2.3.4", "username", "password", min_size=1, max_size=5)

        client = pool.get()
        pool.put(client)
        new_client = pool.get()
        # new_client and client are the same client
        self.assertEqual(client, new_client)

    def test_get_different_client(self):
        self.connect_mock.side_effect = [Mock(), Mock()]

        pool = SSHPool("1.2.3.4", "username", "password", min_size=1, max_size=5)
        client = pool.get()
        new_client = pool.get()

        # !important: you must put the client back to the pool, otherwise the code will be blocked in pool deletion.
        pool.put(client)
        pool.put(new_client)
        self.assertNotEqual(client, new_client)
