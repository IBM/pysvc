import logging
from container.storage_agent_service.server import serve
from container.logger.logger import init_logger

if __name__ == '__main__':
    init_logger(logging.DEBUG)
    serve()
