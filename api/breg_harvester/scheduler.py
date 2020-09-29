import datetime
import logging
import math
import pprint
import threading
import time

from apscheduler.jobstores.base import JobLookupError
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Blueprint, current_app, request
from werkzeug.exceptions import BadRequest, NotFound

from breg_harvester.config import AppConfig
from breg_harvester.harvest import enqueue_harvest_job
from breg_harvester.models import SourceDataset
from breg_harvester.utils import (no_cache_headers, redis_kwargs_from_url,
                                  to_json)

_logger = logging.getLogger(__name__)

BLUEPRINT_NAME = "scheduler"
blueprint = Blueprint(BLUEPRINT_NAME, __name__)

DEFAULT_INTERVAL_SECONDS = 5 * 24 * 3600
PERIODIC_WAKEUP_INTERVAL_SECONDS = 180
PERIODIC_WAKEUP_SUFFIX = "wakeup"


def run_scheduled_harvest(app_config):
    sources = SourceDataset.from_env()

    if not sources or len(sources) == 0:
        _logger.info("Undefined data sources: Skipping scheduled job")
        return None

    return enqueue_harvest_job(sources, app_config=app_config)


def run_scheduled_wakeup():
    """In our setup we run a single instance of APScheduler
     in the Flask app master (with gunicorn --preload). 
     However, this causes the scheduler not to wake up 
     when jobs are updated through the HTTP API. 
     This function exists to force the scheduler to wake up 
     periodically and avoid missing job executions."""

    pass


def get_wakeup_job_id(job_id):
    return f"{job_id}_{PERIODIC_WAKEUP_SUFFIX}"


def add_scheduled_harvest(app, job_id=None, interval=None, force=False):
    job_id = job_id if job_id else app.config.get("SCHEDULER_JOB_ID")

    if not job_id:
        raise Exception("Undefined scheduler job ID")

    job = app.apscheduler.get_job(job_id)

    if job and force:
        remove_scheduled_harvest(app=app, job_id=job_id)
    elif job and not force:
        _logger.debug("Existing scheduled job: %s", job)
        return None

    app_config = {
        key: val for key, val in app.config.items()
        if key in [item.value for item in AppConfig]
    }

    interval = int(interval) if interval else DEFAULT_INTERVAL_SECONDS

    job_kwargs = {
        "func": run_scheduled_harvest,
        "id": job_id,
        "kwargs": {"app_config": app_config},
        "trigger": "interval",
        "seconds": interval
    }

    job_id_wakeup = get_wakeup_job_id(job_id=job_id)

    job_kwargs_wakeup = {
        "func": run_scheduled_wakeup,
        "id": job_id_wakeup,
        "trigger": "interval",
        "seconds": PERIODIC_WAKEUP_INTERVAL_SECONDS
    }

    _logger.debug(
        "Adding scheduled harvest job:\n%s",
        pprint.pformat(job_kwargs))

    _logger.debug(
        "Adding scheduled wakeup job:\n%s",
        pprint.pformat(job_kwargs_wakeup))

    app.apscheduler.add_job(**job_kwargs)
    app.apscheduler.add_job(**job_kwargs_wakeup)

    return app.apscheduler.get_job(job_id)


def remove_scheduled_harvest(app, job_id=None):
    job_id = job_id if job_id else app.config.get("SCHEDULER_JOB_ID")

    try:
        app.apscheduler.remove_job(job_id)
    except JobLookupError:
        pass

    job_id_wakeup = get_wakeup_job_id(job_id=job_id)

    try:
        app.apscheduler.remove_job(job_id_wakeup)
    except JobLookupError:
        pass


def init_scheduler(app):
    redis_url = app.config.get("REDIS_URL")

    if not redis_url:
        raise Exception("Undefined REDIS_URL app config var")

    redis_kwargs = redis_kwargs_from_url(redis_url)

    scheduler_kwargs = {
        "jobstores": {
            "default": RedisJobStore(**redis_kwargs)
        },
        "job_defaults": {
            "coalesce": True,
            "max_instances": 1
        },
        "executors": {
            "default": {
                "type": "threadpool"
            }
        }
    }

    _logger.debug(
        "APScheduler configuration:\n%s",
        pprint.pformat(scheduler_kwargs))

    apscheduler = BackgroundScheduler(**scheduler_kwargs)
    app.apscheduler = apscheduler
    app.apscheduler.start()

    add_scheduled_harvest(app, force=False)

    _logger.info("Running scheduler: %s", app.apscheduler)


def _get_next_date(base_date, seconds):
    tstamp_base = time.mktime(base_date.timetuple())
    tstamp_diff = time.time() - tstamp_base

    if tstamp_diff <= 0:
        return base_date

    interval_rest = math.ceil(tstamp_diff / float(seconds))
    tstamp_next = tstamp_base + interval_rest * seconds

    return datetime.datetime.fromtimestamp(tstamp_next)


def scheduler_job_to_json(scheduler_job):
    seconds = scheduler_job.trigger.interval.total_seconds()
    next_date = scheduler_job.trigger.start_date

    return to_json({
        "id": scheduler_job.id,
        "name": scheduler_job.name,
        "interval_seconds": seconds,
        "next_date": _get_next_date(next_date, seconds)
    })


@blueprint.route("/", methods=["GET"])
def get_scheduled_job():
    job_id = current_app.config.get("SCHEDULER_JOB_ID")

    if not job_id:
        raise NotFound("Undefined job ID")

    job = current_app.apscheduler.get_job(job_id)

    if not job:
        raise NotFound(f"Job {job_id} not found")

    return scheduler_job_to_json(job)


@blueprint.route("/", methods=["POST"])
def update_scheduled_job():
    body = request.get_json()

    try:
        interval_seconds = int(body.get("interval"))
    except:
        raise BadRequest()

    job = add_scheduled_harvest(
        current_app,
        interval=interval_seconds,
        force=True)

    _logger.info("Updated scheduled harvest job: %s", job)

    return scheduler_job_to_json(job)
