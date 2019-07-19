import logging
import sys


def init_logger(log_level):
    root = logging.getLogger()
    root.setLevel(log_level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    formatter = logging.Formatter(
        '%(asctime)s %(name)s: %(levelname)s [%(processName)s][%(process)d] %(pathname)s:%(lineno)d %(message)s'
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)
