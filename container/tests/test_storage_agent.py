from unittest import TestCase
from munch import Munch
from mock import patch, Mock, NonCallableMagicMock
from container.storage_agent_service.storage_agent import get_agent, get_agents, clear_agents
from container.storage_agent_service.util import errors
from pysvc.unified.response import CLIFailureError


class TestStorageAgent(TestCase):

    def setUp(self):
        self.mock_client = NonCallableMagicMock()
        connect_patcher = patch('container.storage_agent_service.util.ssh_utils.connect')
        connect_mock = connect_patcher.start()
        connect_mock.return_value = self.mock_client
        self.addCleanup(connect_patcher.stop)

        self.agent = get_agent("1.2.3.4", "username", "password")

    def tearDown(self):
        clear_agents()

    def test_get_same_agent(self):
        new_agent = get_agent("1.2.3.4", "username", "password")
        self.assertEqual(new_agent, self.agent)

    def test_get_different_agent(self):
        agent_with_other_endpint = get_agent("5.6.7.8", "username", "password")
        agent_with_other_user = get_agent("1.2.3.4", "username1", "password")
        self.assertNotEqual(agent_with_other_endpint, self.agent)
        self.assertNotEqual(agent_with_other_user, self.agent)
        self.assertEqual(3, len(get_agents()))

    def test_get_agent_delete_stale_agent_with_old_password(self):
        agent_with_other_password = get_agent("1.2.3.4", "username", "password1")
        self.assertNotEqual(agent_with_other_password, self.agent)
        # old client is removed
        self.assertEqual(1, len(get_agents()))

    def test_create_host_failed_with_existing_error(self):
        self.mock_client.svctask.mkhost.side_effect = CLIFailureError(message=errors.object_exists)
        # no error will be raised
        self.agent.create_host("h1")

    def test_create_host_failed_with_other_error(self):
        e = CLIFailureError(message="CMMVC9999E")
        self.mock_client.svctask.mkhost.side_effect = e
        with self.assertRaises(CLIFailureError) as cm:
            self.agent.create_host("h1")
            self.assertEqual(e, cm.exception)

    def test_delete_host_failed_with_not_existing_error(self):
        self.mock_client.svctask.rmhost.side_effect = CLIFailureError(message=errors.object_not_exists)
        # no error will be raised
        self.agent.delete_host("h1")

    def test_delete_host_failed_with_other_error(self):
        e = CLIFailureError(message="CMMVC9999E")
        self.mock_client.svctask.rmhost.side_effect = e
        with self.assertRaises(CLIFailureError) as cm:
            self.agent.delete_host("h1")
            self.assertEqual(e, cm.exception)

    def test_get_hosts(self):
        self.mock_client.svcinfo.lshost.return_value = [Munch(id="1", name="h1", status="online")]
        hosts = self.agent.get_hosts()
        self.assertEqual(1, len(hosts))
        self.assertEqual("1", hosts[0].id)

