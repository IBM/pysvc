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
'''Unified SSH client for IBM Spectrum Virtualize Family Storage

Example:

>>> from pysvc.unified import connect
>>> conn = connect('ip', username='admin', privatekey_filename=r'/local/key')
>>> conn.get_device_info() # get device information of storage array
('svc', [('svc', '6.2')])
>>>
>>> dir(conn) # list available commands
[..., 'svcinfo', ...]
>>> dir(conn.svcinfo)
[..., 'lscluster', ...]
>>>
>>> print conn.svcinfo.lscluster.__doc__ # get help
Help on lscluster(**kwargs): ...
>>>
>>> for cluster in conn.svcinfo.lscluster():
...     print cluster
...
..., name = 'cluster1', ...
..., name = 'cluster2', ...
..., name = 'cluster3', ...
>>>
>>> conn.close() # close the connection
'''

from pysvc.unified.client import connect

__all__ = ['connect']
