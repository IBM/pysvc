from pysvc.unified.client import connect
from pysvc.unified.response import CLIFailureError
from .util.ssh_utils import SSHPool
from .util.errors import ErrorPreprocessor
import logging

logger = logging.getLogger(__name__)
_array_agents = []


def get_agent(endpoint, username, password):
    for found in filter(lambda a: a.endpoint == endpoint and a.username == username, _array_agents):
        # delete the agent and clear all the connections if password is changed.
        if found.password != password:
            _array_agents.remove(found)
            del found
        else:
            return found
    agent = StorageAgent(endpoint, username, password)
    _array_agents.append(agent)
    return agent


def get_agents():
    return _array_agents


def clear_agents():
    try:
        while True:
            agent = _array_agents.pop()
            # close all the connections
            del agent
    except IndexError:
        pass


class StorageAgent(object):

    def __init__(self, endpoint, username, password):
        self.username = username
        self.password = password
        self.endpoint = endpoint
        self.client = None
        self.sshpool = None
        self._is_connected = False

        self.sshpool = SSHPool(
            self.endpoint,
            self.username,
            self.password,
            min_size=1,
            max_size=5)

        # self.connect()

    def connect(self):
        self.client = connect(self.endpoint, username=self.username, password=self.password)
        self._is_connected = True

    def disconnect(self):
        if self.client:
            self.client.close()
            self.client = None
            self._is_connected = False

    def __del__(self):
        if self.sshpool:
            # close all the connections
            ssh_pool = self.sshpool
            self.sshpool = None
            del ssh_pool

    def create_host(self, name, iscsi_ports=None, fc_ports=None):
        logger.info("Creating host, name: {}, ports: {}".format(name, fc_ports or iscsi_ports))
        cli_kwargs = {'name': name}
        # fc only, if both fc and iscsi ports are not empty.
        if fc_ports:
            cli_kwargs.update({'fcwwpn': ",".join(fc_ports)})
        elif iscsi_ports:
            cli_kwargs.update({'iscsiname': ",".join(iscsi_ports)})

        try:
            with self.sshpool.item() as client:
                client.svctask.mkhost(**cli_kwargs)
                logger.info("Created host {}".format(name))
        except CLIFailureError as e:
            is_error, _, _ = ErrorPreprocessor(e, logger).process()
            if is_error:
                try:
                    self.delete_host(name)
                except CLIFailureError:
                    pass
                raise

    def delete_host(self, unique_key):
        logger.info("Deleting host {}".format(unique_key))
        cli_kwargs = {'host_name': unique_key}
        try:
            with self.sshpool.item() as client:
                client.svctask.rmhost(**cli_kwargs)
                logger.info("Deleted host {}".format(unique_key))
        except CLIFailureError as e:
            is_error, _, _ = ErrorPreprocessor(e, logger, skip_not_existing_object=True).process()
            if is_error:
                raise

    def get_hosts(self, name=""):
        if name:
            logger.info("Listing host {}".format(name))
        else:
            logger.info("Listing host")
        cli_kwargs = {}
        if name:
            cli_kwargs.update({'filtervalue': 'name={}'.format(name)})
        with self.sshpool.item() as client:
            hosts = client.svcinfo.lshost(**cli_kwargs)
            logger.info("Listed host")
            return hosts
