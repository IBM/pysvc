import re

error_code_pattern = re.compile(r'CMMVC[0-9]+[EW]')
object_exists = "CMMVC6035E"
object_not_exists = "CMMVC5753E"


def extract_error_code(error_str):
    codes = error_code_pattern.findall(error_str)
    if not codes:
        return ""
    else:
        return codes[0]


def is_warning_message(error_code):
    if error_code[-1] == 'W':
        return True
    return False


def is_object_exists(error_code):
    return error_code == object_exists


def is_object_not_exists(error_code):
    return error_code == object_not_exists


class ErrorPreprocessor(object):

    def __init__(self, error, logger=None, skip_not_existing_object=False):
        self.error = error
        self.logger = logger
        self.skip_not_existing_object=skip_not_existing_object

    def process(self):
        """
        process the error

        :return: if_it_is_an_error, error_code, origin_error
        :rtype: tuple
        """

        error_code = extract_error_code(str(self.error))
        if not error_code:
            return False, "", self.error

        if is_warning_message(error_code) or is_object_exists(error_code):
            if self.logger:
                self.logger.warning("action succeeded with warning: {}".format(self.error))
            return False, error_code, self.error

        if self.skip_not_existing_object and is_object_not_exists(error_code):
            if self.logger:
                self.logger.warning("action succeeded with warning: {}".format(self.error))
            return False, error_code, self.error

        if self.logger:
            self.logger.error("action failed with error: {}".format(self.error))
        return True, error_code, self.error







