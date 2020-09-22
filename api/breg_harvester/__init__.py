import logging
import os

level = os.getenv("HARVESTER_LOG_LEVEL", logging.INFO)
logger = logging.getLogger(__name__.split(".")[0])

try:
    import coloredlogs
    coloredlogs.install(level=level, logger=logger)
except ImportError:
    pass
