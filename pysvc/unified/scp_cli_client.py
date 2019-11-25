from socket import timeout as _SocketTimeout
from contextlib import closing
from pysvc.unified.errors import SCPError, SCPTimeoutError

MSG_PART = 3
SIZE_INDEX = 1
CMD_INDEX = 0
SCP_CMD = 'scp -f {path}'
MSG_BUF_DEFUALT_SIZE = 16*1024
FILE_BUF_DEFUALT_SIZE = 64*1024


class ScpClient(object):

    def __init__(self, transport, timeout=None):
        """
        :param transport: ssh transport, e.g.
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(hostname, username=username, password=password)
                self.transport = client.get_transport()
        :param timeout: int, timeout for ssh session
        :return:
        """
        self.transport = transport
        self.timeout = timeout
        # The buf for msg, should greater than msg size
        self.msg_buf_size = MSG_BUF_DEFUALT_SIZE
        # The buf for file, should greater then file size
        self.file_buf_size = FILE_BUF_DEFUALT_SIZE

    def set_msg_buf_size(self, size):
        self.msg_buf_size = size

    def set_file_buf_size(self, size):
        self.file_buf_size = size

    def receive(self, remote_path):
        """
        scp the remote_path
        :param remote_path: str, the full path of the remote file
        :return: str, context of the remote file
        """

        result = None
        scp_cmd = SCP_CMD.format(path=remote_path)
        with closing(self._ssh_open_channel()) as channel:
            # Execute the scp command on the far side.
            channel.exec_command(scp_cmd)
            while not channel.closed:
                channel.sendall('\x00')
                msg = self._scp_recv(channel, self.msg_buf_size)

                if not msg:
                    break

                cmd = msg[CMD_INDEX]
                msg = msg[SIZE_INDEX:]

                if cmd == 'T':
                    pass
                elif cmd == 'C':
                    # Receive file.
                    result = self._scp_receive_file(channel, msg)
                    break
                elif cmd == '\x01':
                    raise SCPError('scp error: {0!r}'.format(msg))
                else:
                    raise SCPError('Unknown scp reply: {0!r} {1!r}'
                                   .format(cmd, msg))

            return result

    def _ssh_open_channel(self):
        """
        Open the ssh session for SCP
        :return: ssh session
        """
        channel = self.transport.open_session()
        if self.timeout is not None:
            channel.settimeout(self.timeout)
        return channel

    @staticmethod
    def _scp_recv(channel, buf_size):
        """
        Receive a part (buf_size byte) of file
        :param buf_size: int, the size of buffer to receive
        :return: str, the receive context
        """
        try:
            return channel.recv(buf_size).decode()
        except _SocketTimeout:
            raise SCPTimeoutError('Timeout waiting for scp response')

    def _scp_receive_file(self, channel, msg):
        """
        Read a remote file, yield parts of the file, until EOF.
        :param channel: ssh session obj,
        :param msg: str, the status of file
        :return: str, the context of the file
        """

        size = self._extract_file_size_info(msg)
        result = ""
        try:
            # Tell the remote side we're ready to read
            channel.sendall('\x00')

            bytes_read = 0
            while bytes_read < size:
                # Compute the max to read.
                bytes_to_read = self.file_buf_size
                if size - bytes_read <= self.file_buf_size:
                    bytes_to_read = size - bytes_read

                s = self._scp_recv(channel, bytes_to_read)

                result += s

                bytes_read += len(s)

            # determine the end of the file
            msg = self._scp_recv(channel, self.msg_buf_size)
            if len(msg) == 0:
                raise SCPError('Error on end of read: msg is empty')

            if msg[CMD_INDEX] != '\x00':
                raise SCPError('Error on end of read: {0!r} {1!r}'.format(
                    msg[CMD_INDEX], msg[SIZE_INDEX:]))

        except _SocketTimeout:
            raise SCPTimeoutError('Timeout on file read')
        return result

    @staticmethod
    def _extract_file_size_info(msg):
        """
        :param msg: str, should contain 'mode size pathname'
        :return: int, the size in the msg
        """

        parts = msg.split()

        if len(parts) != MSG_PART:
            raise SCPError('Invalid file receive header: {0!r}'.format(msg))
        try:
            size = int(parts[SIZE_INDEX])
        except ValueError:
            raise SCPError('Bad file size: {0!r}'.format(parts[1]))

        return size
