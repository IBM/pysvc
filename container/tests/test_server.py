from unittest import TestCase
from unittest.mock import patch
from unittest.mock import NonCallableMagicMock
from munch import Munch
import random

import grpc

from concurrent import futures

from container.generated import storageagent_pb2
from container.generated import storageagent_pb2_grpc
from container.storage_agent_service.server import StorageAgent


class TestServer(TestCase):

    def setUp(self):
        self.mock_client = NonCallableMagicMock()
        connect_patcher = patch('container.storage_agent_service.util.ssh_utils.connect')
        self.connect_mock = connect_patcher.start()
        self.connect_mock.side_effect = [
            self.mock_client,
            NonCallableMagicMock(),
            NonCallableMagicMock(),
            NonCallableMagicMock(),
            NonCallableMagicMock()
        ]
        self.addCleanup(connect_patcher.stop)

        self._server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        storageagent_pb2_grpc.add_StorageAgentServicer_to_server(StorageAgent(), self._server)

        port = random.randint(50050, 50099)
        self._server.add_insecure_port('unix:///tmp/storage.sock:{}'.format(port))
        self._server.start()

        self._channel = grpc.insecure_channel('unix:///tmp/storage.sock:{}'.format(port))
        self._stub = storageagent_pb2_grpc.StorageAgentStub(self._channel)

    def tearDown(self):
        self._server.stop(None)

    def _test_list_hosts(self):
        self.mock_client.svcinfo.lshost.return_value = [Munch(id="1", name="h1", status="online")]
        response = self._stub.ListHosts(
            storageagent_pb2.ListHostsRequest(
                secrets={"management_address": "1.2.3.4", "username": "username", "password": "password"}),
            timeout=10)
        self.assertEqual(1, len(response.hosts))
        self.assertEqual("1.2.3.4", response.hosts[0].array)

    def test_list_hosts_twice(self):
        # two request should use same client
        self._stub.ListHosts(
            storageagent_pb2.ListHostsRequest(
                secrets={"management_address": "1.2.3.4", "username": "username", "password": "password"}),
            timeout=1)
        self._stub.ListHosts(
            storageagent_pb2.ListHostsRequest(
                secrets={"management_address": "1.2.3.4", "username": "username", "password": "password"}),
            timeout=1)

        # lshost is called twice, while connect is called only once,
        # means that two requests use same client
        self.assertEqual(2, self.mock_client.svcinfo.lshost.call_count)
        self.assertEqual(1, self.connect_mock.call_count)
