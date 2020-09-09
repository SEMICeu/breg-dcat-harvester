import datetime
import json


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


def job_to_json(job):
    return to_json({
        "job_id": job.id,
        "description": job.description,
        "status": job.get_status(),
        "result": job.result,
        "enqueued_at": job.enqueued_at,
        "started_at": job.started_at,
        "ended_at": job.ended_at
    })
