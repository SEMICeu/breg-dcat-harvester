import logging
import pprint

import redis
from flask import Blueprint, current_app, g, jsonify, request
from rdflib import Graph
from SPARQLWrapper import SPARQLWrapper
from werkzeug.exceptions import NotFound, ServiceUnavailable

import breg_harvester.jobs_queue
import breg_harvester.store
import breg_harvester.utils
from breg_harvester.models import SourceDataset
from breg_harvester.validator import get_validator

_logger = logging.getLogger(__name__)

BLUEPRINT_NAME = "harvest"
blueprint = Blueprint(BLUEPRINT_NAME, __name__)


def run_harvest(sources, store_kwargs=None, validator=None, graph_uri=None):
    if not validator:
        validator = get_validator()

    if not graph_uri:
        graph_uri = current_app.config.get("GRAPH_URI")

    store_kwargs = store_kwargs if store_kwargs else {}

    _logger.info("Running harvest:\n%s", pprint.pformat({
        "sources": sources,
        "store_kwargs": store_kwargs,
        "validator": validator,
        "graph_uri": graph_uri
    }))

    store = breg_harvester.store.get_sparql_store(**store_kwargs)
    store_graph = Graph(store, identifier=graph_uri)

    err_sources = [
        source for source in sources
        if not validator.validate(source)
    ]

    if len(err_sources) > 0:
        raise ValueError(f"Invalid sources:\n{pprint.pformat(err_sources)}")

    breg_harvester.store.set_store_header_update(store)

    for source in sources:
        _logger.debug("Parsing: %s", source)
        store_graph.parse(source.uri, format=source.rdflib_format)

    breg_harvester.store.set_store_header_read(store)

    res = {
        "num_triples": len(store_graph),
        "sources": [item.to_dict() for item in sources]
    }

    _logger.info("Harvest result:\n%s", pprint.pformat(res))

    store_graph.close()

    return res


@blueprint.route("/source", methods=["GET"])
def get_sources():
    try:
        sources = SourceDataset.from_env()
    except Exception as ex:
        raise ServiceUnavailable(f"Error reading data sources: {str(ex)}")

    if not sources:
        return jsonify(None)

    return jsonify([source.to_dict() for source in sources])


def enqueue_harvest_job(sources, app_config=None):
    app_config = app_config if app_config else current_app.config

    connection = None

    if app_config:
        redis_url = app_config.get("REDIS_URL")
        connection = redis.from_url(redis_url)

    rqueue = breg_harvester.jobs_queue.get_queue(connection=connection)

    store_kwargs = {
        "query_endpoint": app_config.get("SPARQL_ENDPOINT"),
        "update_endpoint": app_config.get("SPARQL_UPDATE_ENDPOINT"),
        "sparql_user": app_config.get("SPARQL_USER"),
        "sparql_pass": app_config.get("SPARQL_PASS")
    }

    validator = get_validator(app_config=app_config)
    graph_uri = app_config.get("GRAPH_URI")

    harvest_kwargs = {
        "sources": sources,
        "store_kwargs": store_kwargs,
        "validator": validator,
        "graph_uri": graph_uri
    }

    _logger.info(
        "Enqueuing new harvest job:\n%s",
        pprint.pformat(harvest_kwargs))

    result_ttl = app_config.get("RESULT_TTL")

    job = rqueue.enqueue(
        run_harvest,
        result_ttl=result_ttl,
        kwargs=harvest_kwargs)

    return breg_harvester.utils.job_to_json(job)


@blueprint.route("/", methods=["POST"])
def create_harvest_job():
    try:
        sources = SourceDataset.from_env()
    except Exception as ex:
        raise ServiceUnavailable(f"Error reading data sources: {str(ex)}")

    if not sources or len(sources) == 0:
        raise ServiceUnavailable("Undefined data sources")

    return enqueue_harvest_job(sources)


@blueprint.route("/<job_id>", methods=["GET"])
def get_harvest_job(job_id):
    rqueue = breg_harvester.jobs_queue.get_queue()
    job = rqueue.fetch_job(job_id)

    if not job:
        raise NotFound()

    return breg_harvester.utils.job_to_json(job)


def _fetch_registry_jobs(reg, rqueue, num, extended):
    jobs = [
        rqueue.fetch_job(jid)
        for jid in reg.get_job_ids(start=-num)
    ]

    return [
        breg_harvester.utils.job_to_json(job, extended=extended)
        for job in jobs
    ]


@blueprint.route("/", methods=["GET"])
def get_harvest_jobs():
    num = int(request.args.get("num", 10))
    extended = bool(request.args.get("extended", False))
    rqueue = breg_harvester.jobs_queue.get_queue()

    jobs_finished = _fetch_registry_jobs(
        reg=rqueue.finished_job_registry,
        rqueue=rqueue,
        num=num,
        extended=extended)

    jobs_failed = _fetch_registry_jobs(
        reg=rqueue.failed_job_registry,
        rqueue=rqueue,
        num=num,
        extended=extended)

    jobs_scheduled = _fetch_registry_jobs(
        reg=rqueue.scheduled_job_registry,
        rqueue=rqueue,
        num=num,
        extended=extended)

    jobs_started = _fetch_registry_jobs(
        reg=rqueue.started_job_registry,
        rqueue=rqueue,
        num=num,
        extended=extended)

    return {
        "finished": jobs_finished,
        "failed": jobs_failed,
        "scheduled": jobs_scheduled,
        "started": jobs_started
    }
