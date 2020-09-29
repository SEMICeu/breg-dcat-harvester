import logging
import os

level = os.getenv("HARVESTER_LOG_LEVEL", logging.INFO)
logger = logging.getLogger(__name__.split(".")[0])
logger_scheduler = logging.getLogger("apscheduler")

try:
    import coloredlogs
    coloredlogs.install(level=level, logger=logger)
    coloredlogs.install(level=level, logger=logger_scheduler)
except ImportError:
    pass
