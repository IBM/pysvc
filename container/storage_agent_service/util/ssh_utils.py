from eventlet import pools
from pysvc.unified.client import connect
import logging

logger = logging.getLogger(__name__)


class SSHPool(pools.Pool):
    """A simple eventlet pool to hold ssh connections."""

    def __init__(self, ip, username, password, port=22,
                 *args, **kwargs):
        self.ip = ip
        self.username = username
        self.password = password
        self.port = port
        self.current_size = 0

        super(SSHPool, self).__init__(*args, **kwargs)

    def __del__(self):
        if not self.current_size:
            return
        # change the size of the pool to reduce the number
        # of elements on the pool via puts.
        self.resize(1)
        # release all but the last connection using
        # get and put to allow any get waiters to complete.
        while self.waiting() or self.current_size > 1:
            conn = self.get()
            self.put(conn)
        # Now free everything that is left
        while self.free_items:
            self.free_items.popleft().close()
            self.current_size -= 1

    def create(self):
        try:
            return connect(self.ip, username=self.username, password=self.password, port=self.port)
        except Exception:
            raise

    def get(self):
        """Return an item from the pool, when one is available.

        This may cause the calling greenthread to block. Check if a
        connection is active before returning it.

        For dead connections create and return a new connection.
        """
        client = super(SSHPool, self).get()
        if client:
            if client.transport.transport.get_transport().is_active():
                return client
            else:
                client.close()
        try:
            logger.debug(
                "A client is inactive, Creating a new client, "
                "current clients is {}".format(self.current_size)
            )
            new_client = self.create()
        except Exception:
            if client:
                self.current_size -= 1
            raise
        return new_client

    def put(self, client):
        # If we have more connections then we should just close it
        if self.current_size > self.max_size:
            client.close()
            self.current_size -= 1
            return
        super(SSHPool, self).put(client)

    def remove(self, client):
        """Close an ssh client and remove it from free_items."""
        client.close()
        if client in self.free_items:
            self.free_items.remove(client)
            if self.current_size > 0:
                self.current_size -= 1
