import grpc

from ..generated import storageagent_pb2
from ..generated import storageagent_pb2_grpc

# Note: it is an sample client to test the storage agent service functionality.


def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    #
    # For more channel options, please see https://grpc.io/grpc/core/group__grpc__arg__keys.html
    with grpc.insecure_channel(
            target='unix:///tmp/csi.sock:10086',
            options=[('grpc.lb_policy_name', 'pick_first'),
                     ('grpc.enable_retries', 0), ('grpc.keepalive_timeout_ms',
                                                  10000)]) as channel:
        stub = storageagent_pb2_grpc.StorageAgentStub(channel)

        hostname = "h1"
        secret = {"management_address": "1.2.3.4", "username": "username", "password": "password"}
        print("Creating host {}".format(hostname))
        # Timeout in seconds.
        # Please refer gRPC Python documents for more detail. https://grpc.io/grpc/python/grpc.html
        response = stub.CreateHost(
            storageagent_pb2.CreateHostRequest(
                name=hostname, iqns=["iqn-1", "iqn-2"], wwpns=[],
                secrets=secret),
            timeout=10)
        print("Created host: {}".format(response.host))

        print("Listing all hosts")
        response = stub.ListHosts(
            storageagent_pb2.ListHostsRequest(
                secrets=secret),
            timeout=10)
        print("Listed all hosts: {}".format(response.hosts))

        print("Listing host {}".format(hostname))
        response = stub.ListHosts(
            storageagent_pb2.ListHostsRequest(
                name=hostname,
                secrets=secret),
            timeout=10)
        print("Listed host: {}".format(response.hosts))

        print("Deleting host {}".format(hostname))
        stub.DeleteHost(
            storageagent_pb2.DeleteHostRequest(
                name=hostname,
                secrets=secret),
            timeout=10)
        print("Deleted host")
