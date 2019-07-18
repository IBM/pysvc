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

# ------------- Transport ---------------------


class TransportMessages(object):
    TRANSPORT_DISCONNECT = 'Transport is disconnected'
    SSH_INCORRECT_PRIVATE_KEY = 'Private key incorrect'
    SSH_FAILED_TO_LOAD_KNOWN_HOSTS = 'Failed to load known hosts file'
    SSH_PASS_PHRASE_REQUIRED = 'Check if password was specified to unlock ' \
                               'the private key file'
    SSH_AUTHENTICATION_FAILURE = 'Authentication failed'
    SSH_CONNECT_TIMED_OUT = 'Timed out when attempting to establish ' \
                            'a ssh connection'
    SSH_CON_TIMED_OUT_WHEN_EXEC_CMD = 'Timed out when executing command ' \
                                      'through a ssh connection, possibly ' \
                                      'the command is interactive'

    @staticmethod
    def SSH_UNABLE_TO_CONNECT(host):
        return 'Cannot establish ssh connection to %s' % host

    @staticmethod
    def SSH_ALLOWED_AUTH_TYPES(types):
        return 'Allowed authentication types are: %s' % types

    @staticmethod
    def SSH_BAD_HOST_FINGERPRINT(host):
        return 'Host finger print does not match when connect to %s. Add ' \
               'correct host key in xsf_known_hosts to get rid of ' \
               'this exception.' % host

    @staticmethod
    def SSH_HOST_DOES_NOT_EXIST(host):
        return 'Cannot establish the ssh connection to %s due to ' \
               'unrecognizable host' % host

# ------------- Unified ---------------------


class UnifiedMessages(object):
    UNIFIED_PARSE_LOCAL_START = 'Try to parse local CLI specification'
    UNIFIED_NO_CLI_SPEC = 'No CLI specification is not found'
    UNIFIED_PARSE_REMOTE_FAIL = 'It fails to parse the CLI specification ' \
                                'from storage array.'
    SSH_NO_ENDPOINT_PROVIDED = 'No ssh connection endpoint provided'
    SVCCLI_UNKNOWN_ARRAY = 'SVCCLI: Unknown array'

    @staticmethod
    def UNIFIED_INCORRECT_DEVICE_TYPE(device):
        return 'The expected device %s is not found.' % (device)

    @staticmethod
    def UNIFIED_CATXMLSPEC_FAIL(err):
        return 'The storage array fails to run "catxmlspec" command: %s' % (
            err)
