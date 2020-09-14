import datetime
import json
import logging

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
