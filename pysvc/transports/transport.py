##############################################################################
# Copyright 2025 IBM Corp.
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


class CommonTransport(object):
    def connect(self):
        raise NotImplementedError(
            "This interface should be called from subclass instances.")

    def send_command(self, command):
        raise NotImplementedError(
            "This interface should be called from subclass instances.")

    def __repr__(self):
        if self.connected_endpoint:
            return '<%s (%s)>' % (self.__class__.__name__,
                                  self.connected_endpoint)
        return '<%s>' % self.__class__.__name__

    def __str__(self):
        if self.connected_endpoint:
            return str(self.connected_endpoint)
        return TransportMessages.TRANSPORT_DISCONNECT
