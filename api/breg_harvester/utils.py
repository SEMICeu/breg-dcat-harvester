import datetime
import json
import logging
from functools import update_wrapper, wraps

import redis
from flask import make_response

_logger = logging.getLogger(__name__)


def to_json(val):
    if isinstance(val, dict):
        return {key: to_json(val) for key, val in val.items()}

    if isinstance(val, list):
        return [to_json(item) for item in val]

    try:
        # Datetimes
        return val.isoformat()
    except:
        pass

    try:
        json.dumps(val)
        return val
    except:
        return repr(val)


def job_to_json(job, extended=True):
    job_dict = {
        "job_id": job.id,
        "status": job.get_status(),
        "enqueued_at": job.enqueued_at,
        "started_at": job.started_at,
        "ended_at": job.ended_at
    }

    if extended:
        job_dict.update({
            "description": job.description,
            "result": job.result,
            "exc_info": job.exc_info
        })

    return to_json(job_dict)


def redis_kwargs_from_url(redis_url):
    client = redis.from_url(redis_url)
    conn_kwargs = client.connection_pool.connection_kwargs
    client.connection_pool.disconnect()

    _logger.debug(
        "Redis connection args for URL '%s': %s",
        redis_url, conn_kwargs)

    return conn_kwargs


def no_cache_headers(view):
    """Attribution to:
    https://arusahni.net/blog/2014/03/flask-nocache.html"""

    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers["Last-Modified"] = datetime.datetime.now()
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "-1"
        return response

    return update_wrapper(no_cache, view)
