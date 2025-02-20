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

import sys
import traceback


def chained(wrapping_exc):
    # pylint: disable=W0212
    """
    Embeds the current exception information into the given one (which
    will replace the current one).
    For example::

        try:
            ...
        except OSError as ex:
            raise chained(MyError("database not found!"))
    """
    t, v, tb = sys.exc_info()
    if not t:
        return wrapping_exc
    wrapping_exc._inner_exc = v
    lines = traceback.format_exception(t, v, tb)
    wrapping_exc._inner_tb = "".join(lines[1:])
    return wrapping_exc
