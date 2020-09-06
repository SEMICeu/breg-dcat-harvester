import logging
import os

import redis
from flask import current_app, g
from rq import Queue

ENV_TIMEOUT = "BREG_TIMEOUT"
DEFAULT_TIMEOUT = 1800
QUEUE_NAME = "breg-harvester"

_logger = logging.getLogger(__name__)


def get_queue(connection):
    default_timeout = int(os.getenv(ENV_TIMEOUT, DEFAULT_TIMEOUT))

    return Queue(
        name=QUEUE_NAME,
        connection=connection,
        default_timeout=default_timeout)


def get_redis():
    if "redis" not in g:
        redis_url = current_app.config.get("REDIS_URL")
        redis_client = redis.from_url(redis_url)
        g["redis"] = redis_client

    return g.get("redis")


def close_redis(e=None):
    redis_client = g.pop("redis", None)

    if redis_client is None:
        return

    try:
        redis_client.connection_pool.disconnect()
    except:
        _logger.warning("Error closing Redis", exc_info=True)


def init_app_redis(app):
    app.teardown_appcontext(close_redis)
