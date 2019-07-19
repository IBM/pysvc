from concurrent import futures
import os
import time
import logging


import grpc
from grpc_reflection.v1alpha import reflection

from ..generated import storageagent_pb2
from ..generated import storageagent_pb2_grpc
from ..storage_agent_service.storage_agent import get_agent

_ONE_DAY_IN_SECONDS = 60 * 60 * 24
logger = logging.getLogger(__name__)


class StorageAgent(storageagent_pb2_grpc.StorageAgentServicer):

    def CreateHost(self, request, context):
        user = request.secrets["username"]
        password = request.secrets["password"]
        endpoint = request.secrets["management_address"]

        agent = get_agent(endpoint, user, password)
        agent.create_host(request.name, iscsi_ports=request.iqns, fc_ports=request.wwpns)
        for host in agent.get_hosts(request.name):
            return storageagent_pb2.CreateHostReply(
                host=storageagent_pb2.Host(
                    identifier=host.id,
                    name=host.name,
                    status=host.status,
                    array=endpoint,
                    iqns=request.iqns,
                    wwpns=request.wwpns,
                )
            )

    def DeleteHost(self, request, context):
        user = request.secrets["username"]
        password = request.secrets["password"]
        endpoint = request.secrets["management_address"]

        agent = get_agent(endpoint, user, password)
        agent.delete_host(request.name)
        return storageagent_pb2.DeleteHostReply()

    def ListHosts(self, request, context):
        user = request.secrets["username"]
        password = request.secrets["password"]
        endpoint = request.secrets["management_address"]

        agent = get_agent(endpoint, user, password)
        hosts = []
        for host in agent.get_hosts(request.name):
            hosts.append(
                storageagent_pb2.Host(
                    identifier=host.id,
                    name=host.name,
                    status=host.status,
                    array=endpoint,
                )
            )
        return storageagent_pb2.ListHostsReply(hosts=hosts)


def generate_server_config():
    config = {}
    address = os.environ.get("ENDPOINT")
    if not address:
        raise Exception("env ENDPOINT is not set")
    config["address"] = address
    config["max_workers"] = os.environ.get("WORKERS", 10)
    return config


def serve():
    config = generate_server_config()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=config["max_workers"]))
    storageagent_pb2_grpc.add_StorageAgentServicer_to_server(StorageAgent(), server)
    service_names = (
        storageagent_pb2.DESCRIPTOR.services_by_name['StorageAgent'].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(service_names, server)
    server.add_insecure_port(config["address"])
    logger.info("Starting server")
    server.start()
    logger.info("Server is started")
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)
        logger.info("Server is stopped")
