from unittest import TestCase
from container.storage_agent_service.util import errors

errors_warning = "CLI failure. Return code is 1. Error message is \"b'CMMVC1234W it is a warning.\n'\""
errors_object_exists = "CLI failure. Return code is 1. Error message is \"b'CMMVC6035E The action failed as the object already exists.\n'\""  # noqa
errors_object_not_exists = "CLI failure. Return code is 1. Error message is \"b'CMMVC5753E The specified object does not exist or is not a suitable candidate.\n'\""  # noqa
errors_other_error = "CLI failure. Return code is 1. Error message is \"b'CMMVC6099E it is an error\n'\""


class TestErrors(TestCase):

    def test_is_warning_message(self):
        error_code = errors.extract_error_code(errors_warning)
        self.assertTrue(errors.is_warning_message(error_code))

        error_code = errors.extract_error_code(errors_other_error)
        self.assertFalse(errors.is_warning_message(error_code))

    def test_is_object_exists(self):
        error_code = errors.extract_error_code(errors_object_exists)
        self.assertTrue(errors.is_object_exists(error_code))

        error_code = errors.extract_error_code(errors_other_error)
        self.assertFalse(errors.is_object_exists(error_code))

    def test_is_object_not_exists(self):
        error_code = errors.extract_error_code(errors_object_not_exists)
        self.assertTrue(errors.is_object_not_exists(error_code))

        error_code = errors.extract_error_code(errors_other_error)
        self.assertFalse(errors.is_object_not_exists(error_code))

    def test_process(self):
        for err, is_true in {
            errors_warning: False,
            errors_object_exists: False,
            errors_object_not_exists: True,
            errors_other_error: True
        }.items():
            is_error, _, _ = errors.ErrorPreprocessor(err, logger=None).process()
            self.assertEqual(is_error, is_true)

    def test_process_skip_existing_object(self):
        for err, is_true in {
            errors_warning: False,
            errors_object_exists: False,
            errors_object_not_exists: False,
            errors_other_error: True
        }.items():
            is_error, _, _ = errors.ErrorPreprocessor(err, logger=None, skip_not_existing_object=True).process()
            self.assertEqual(is_error, is_true)
