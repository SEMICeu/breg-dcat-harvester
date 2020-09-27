import logging
import pprint

from apscheduler.jobstores.redis import RedisJobStore
from flask import Blueprint, current_app, request
from flask_apscheduler import APScheduler
from werkzeug.exceptions import BadRequest, NotFound

from breg_harvester.config import AppConfig
from breg_harvester.harvest import enqueue_harvest_job
from breg_harvester.models import SourceDataset
from breg_harvester.utils import (no_cache_headers, redis_kwargs_from_url,
                                  to_json)

_logger = logging.getLogger(__name__)

BLUEPRINT_NAME = "scheduler"
blueprint = Blueprint(BLUEPRINT_NAME, __name__)

SCHEDULED_JOB_ID = "scheduled-harvester"
DEFAULT_INTERVAL_SECONDS = 5 * 24 * 3600


def scheduled_job(app_config):
    sources = SourceDataset.from_env()

    if not sources or len(sources) == 0:
        raise Exception("Undefined data sources")

    return enqueue_harvest_job(sources, app_config=app_config)


def add_scheduled_job(app, interval=None, force=False):
    job = app.apscheduler.get_job(SCHEDULED_JOB_ID)

    if job and force:
        app.apscheduler.remove_job(SCHEDULED_JOB_ID)
    elif job and not force:
        _logger.debug("Existing scheduled job: %s", job)
        return

    app_config = {
        key: val for key, val in app.config.items()
        if key in [item.value for item in AppConfig]
    }

    interval = int(interval) if interval else DEFAULT_INTERVAL_SECONDS

    job_kwargs = {
        "func": scheduled_job,
        "id": SCHEDULED_JOB_ID,
        "kwargs": {"app_config": app_config},
        "trigger": "interval",
        "seconds": interval
    }

    _logger.info(
        "Adding job to %s:\n%s",
        app.apscheduler, pprint.pformat(job_kwargs))

    app.apscheduler.add_job(**job_kwargs)


def init_scheduler(app):
    redis_url = app.config.get("REDIS_URL")

    if not redis_url:
        raise Exception("Undefined REDIS_URL app config var")

    redis_kwargs = redis_kwargs_from_url(redis_url)

    scheduler_conf = {
        "SCHEDULER_JOBSTORES": {
            "default": RedisJobStore(**redis_kwargs)
        },
        "SCHEDULER_EXECUTORS": {
            "default": {
                "type": "threadpool",
                "max_workers": 2
            }
        },
        "SCHEDULER_JOB_DEFAULTS": {
            "coalesce": True,
            "max_instances": 1
        }
    }

    _logger.debug(
        "APScheduler configuration:\n%s",
        pprint.pformat(scheduler_conf))

    app.config.update(scheduler_conf)

    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()

    add_scheduled_job(app, force=False)

    _logger.info("APScheduler running")


def scheduler_job_to_json(scheduler_job):
    return to_json({
        "id": scheduler_job.id,
        "name": scheduler_job.name,
        "interval_seconds": scheduler_job.trigger.interval.total_seconds(),
        "next_date": scheduler_job.trigger.start_date
    })


@blueprint.route("/", methods=["GET"])
@no_cache_headers
def get_scheduled_job():
    job = current_app.apscheduler.get_job(SCHEDULED_JOB_ID)

    if not job:
        raise NotFound()

    return scheduler_job_to_json(job)


@blueprint.route("/", methods=["POST"])
def update_scheduled_job():
    body = request.get_json()

    try:
        interval_seconds = int(body.get("interval"))
    except:
        raise BadRequest()

    add_scheduled_job(current_app, interval=interval_seconds, force=True)
    job = current_app.apscheduler.get_job(SCHEDULED_JOB_ID)

    return scheduler_job_to_json(job)
