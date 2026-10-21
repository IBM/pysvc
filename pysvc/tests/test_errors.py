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
'''Test for the string conversion of pysvc errors'''

import unittest

from pysvc.errors import UnableToConnectException


class TestStorageArrayClientExceptionStr(unittest.TestCase):

    def test_str_with_single_original_exception(self):
        error = UnableToConnectException(
            message='msg', original_exception=ValueError('single'))

        self.assertEqual('msg::single', str(error))

    def test_str_with_list_of_original_exceptions(self):
        error = UnableToConnectException(
            message='msg',
            original_exception=[ValueError('first'), ValueError('second')])

        self.assertEqual('msg::first::second', str(error))

    def test_str_with_tuple_of_original_exceptions(self):
        error = UnableToConnectException(
            message='msg', original_exception=(ValueError('first'),))

        self.assertEqual('msg::first', str(error))

    def test_str_without_original_exception(self):
        error = UnableToConnectException(message='msg')

        self.assertEqual('msg', str(error))

    def test_str_without_message(self):
        error = UnableToConnectException(
            original_exception=ValueError('single'))

        self.assertEqual('::single', str(error))
