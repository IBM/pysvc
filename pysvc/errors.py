##############################################################################
# Copyright 2019 IBM Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
##############################################################################
from pysvc.messages import TransportMessages


class StorageArrayClientException(Exception):
    """
    Base class for generic storge array cleint exceptions.
    """

    def __init__(self, message=None, original_exception=None):
        if message is None and original_exception is None:
            raise ValueError(
                "either message or original_exception must be set")
        self.my_message = message
        self.original_exception = original_exception

    def __str__(self):
        response = ""
        if self.my_message:
            response += str(self.my_message)
        if self.original_exception is not None:
            response += "::" + "::".join(str(ex)
                                         for ex in self.original_exception)

        return response

    def __unicode__(self):
        return str(self.__str__())

# --------------------  Authentication  --------------------


class IncorrectCredentials(StorageArrayClientException):
    pass


class IncorrectUsername(IncorrectCredentials):
    pass


class IncorrectPassword(IncorrectCredentials):
    pass


class UnsupportXmlCompression(StorageArrayClientException):
    pass

# --------------------  SSH Authentication  --------------------


class SSHFailedToLoadKnownHosts(IncorrectCredentials):
    pass


class SSHAuthenticationFailure(IncorrectCredentials):
    pass


class BadAuthenticationTypeException(SSHAuthenticationFailure):
    """
    Exception raised when incorrect authentication types were used.
    """

    def __init__(
            self,
            message=None,
            allowed_types=[],
            original_exception=None):
        super(
            BadAuthenticationTypeException,
            self).__init__(
            message,
            original_exception)
        self._allowed_auth_types = allowed_types

    @property
    def allowed_authentication_types(self):
        return self._allowed_auth_types

    def __str__(self):
        return TransportMessages.SSH_ALLOWED_AUTH_TYPES(
            self._allowed_auth_types)


class PassphraseRequiredException(SSHAuthenticationFailure):
    """
    Exception raised when a pass phrase is absent when
    attempting to unlock the private key.
    """
    pass


class PartialAuthenticationException(SSHAuthenticationFailure):
    """
    Exception raised when a partial authentication was detected.
    """

    def __init__(
            self,
            message=None,
            allowed_types=[],
            original_exception=None):
        super(
            PartialAuthenticationException,
            self).__init__(
            message,
            original_exception)
        self._allowed_auth_types = allowed_types

    @property
    def allowed_authentication_types(self):
        return self._allowed_auth_types

    def __str__(self):
        return TransportMessages.SSH_ALLOWED_AUTH_TYPES(
            self._allowed_auth_types)


class BadHostFingerPrintException(SSHAuthenticationFailure):
    """
    Host finger print given by the server did not match expected one.
    """

    def __init__(
            self,
            message=None,
            hostname=None,
            expected_key=None,
            presented_key=None,
            original_exception=None):
        super(
            BadHostFingerPrintException,
            self).__init__(
            message,
            original_exception)
        self._hostname = hostname
        self._expeted_key = expected_key
        self._presented_key = presented_key
        self._original_exception = original_exception

    @property
    def presented_key(self):
        return self._presented_key

    @property
    def hostname(self):
        return self._hostname

    @property
    def expeted_key(self):
        return self._expected_key

    def __str__(self):
        return TransportMessages.SSH_BAD_HOST_FINGERPRINT(self._hostname)

# --------------------  Connection Error --------------------


class UnableToConnectException(StorageArrayClientException):
    pass


class HostDoesNotExistException(UnableToConnectException):
    """
    Raised when the destination host does not exist.
    """

    def __init__(self, message=None, hostname=None, original_exception=None):
        super(
            HostDoesNotExistException,
            self).__init__(
            message,
            original_exception)
        self._hostname = hostname

    @property
    def hostname(self):
        return self._hostname

    def __str__(self):
        return TransportMessages.SSH_HOST_DOES_NOT_EXIST(self._hostname)


class ConnectionTimedoutException(UnableToConnectException):
    pass


class ProtocolMismatchException(UnableToConnectException):
    pass


class CantInstantiateError(StorageArrayClientException):
    pass

# --------------------  SSL Authentication  --------------------


class SSLAuthenticationFailure(IncorrectCredentials):
    """
    TODO: Combine SSL exceptions into this hierarchy.
    """
    pass

# --------------------  Execution --------------------


class GeneralExecutionError(Exception):
    """
    Base class for generic storge array call execution exception.
    """

    def __init__(self, message=None, original_exception=None):
        if message is None and original_exception is None:
            raise ValueError(
                "either message or original_exception must be set")
        self.my_message = message
        self.original_exception = original_exception

    def _get_error_string(self, error):
        response = ""

        if not isinstance(
                error,
                GeneralExecutionError) or isinstance(
                error,
                CommandExecutionError):
            response += str(error)
        elif hasattr(error, 'my_message'):
            response += str(error.my_message)
        if hasattr(
                error,
                'original_exception') and error.original_exception is not None:
            response += "::" + "::".join(self._get_error_string(ex)
                                         for ex in error.original_exception)

        return response

    def __str__(self):
        return self._get_error_string(self)

    def __unicode__(self):
        return str(self._get_error_string(self))


class UnknownDeviceTypeError(GeneralExecutionError):
    pass


class CommandExecutionError(GeneralExecutionError):
    """
    Base class for storge array command execution exception.
    Do NOT call __str__ from _get_error_string in this class
    and its sub-classes.
    """

    def __init__(
            self,
            message=None,
            command=None,
            response=None,
            original_exception=None):
        super(
            CommandExecutionError,
            self).__init__(
            message,
            original_exception)
        self.my_command = command
        self.my_response = response

    def _get_error_string(self, error):
        response = ""
        if hasattr(error, 'my_command'):
            response += "Storage array command <" + \
                str(error.my_command) + "> failed: "
        if hasattr(error, 'my_response'):
            response += str(error.my_response)

        return response


class ResponseParserError(CommandExecutionError):
    pass


class InternalSystemError(CommandExecutionError):
    pass
