import json
import logging
import pprint

import requests
from flask import Blueprint, current_app, g, jsonify, request
from rdflib import Graph
from requests.auth import HTTPDigestAuth
from SPARQLWrapper import SPARQLWrapper
from werkzeug.exceptions import NotFound

import breg_harvester.queue
import breg_harvester.store
import breg_harvester.utils
from breg_harvester.models import DataTypes, SourceDataset, mime_for_type

_logger = logging.getLogger(__name__)

BLUEPRINT_NAME = "harvest"
blueprint = Blueprint(BLUEPRINT_NAME, __name__)


class APIValidator:
    API_URL = "https://www.itb.ec.europa.eu/shacl/cpsv-ap/api/validate"

    @classmethod
    def build_source_body(cls, source):
        return {
            "contentSyntax": source.mime_type,
            "contentToValidate": source.uri,
            "embeddingMethod": "URL",
            "reportSyntax": mime_for_type(DataTypes.JSONLD)
        }

    def __init__(self, api_url=API_URL):
        self.api_url = api_url

    def validate(self, source):
        try:
            body = self.build_source_body(source)
            _logger.debug("Request validation (%s): %s", self.api_url, body)
            res = requests.post(self.api_url, json=body)
            res_json = json.loads(res.text)
            return res_json.get("sh:conforms", False)
        except:
            _logger.warning("Error on validator API request", exc_info=True)
            return False


class DummyValidator:
    def validate(self, *args, **kwargs):
        _logger.info("Using validator: %s", self.__class__)
        return True


def run_harvest(sources, store_kwargs=None, validator=None, graph_uri=None):
    if not validator:
        validator = APIValidator()
        _logger.debug("Using default validator: %s", validator)

    if not graph_uri:
        graph_uri = current_app.config.get("GRAPH_URI")
        _logger.debug("Using default graph URI: %s", graph_uri)

    store_kwargs = store_kwargs if store_kwargs else {}
    store = breg_harvester.store.get_sparql_store(**store_kwargs)

    store_graph = Graph(store, identifier=graph_uri)

    _logger.info("Original sources:\n%s", pprint.pformat(sources))

    valid_sources = [
        source for source in sources
        if validator.validate(source)
    ]

    _logger.info("Valid sources:\n%s", pprint.pformat(valid_sources))

    breg_harvester.store.set_store_header_update(store)

    for source in valid_sources:
        _logger.debug("Parsing: %s", source)
        store_graph.parse(source.uri, format=source.rdflib_format)

    breg_harvester.store.set_store_header_read(store)

    res = {
        "num_triples": len(store_graph),
        "sources": [item.to_dict() for item in valid_sources]
    }

    _logger.info("Harvest result:\n%s", pprint.pformat(res))

    store_graph.close()

    return res


@blueprint.route("/source", methods=["GET"])
def get_sources():
    sources = SourceDataset.from_env()

    if not sources:
        return jsonify(None)

    return jsonify([source.to_dict() for source in sources])


@blueprint.route("/", methods=["POST"])
def create_harvest_job():
    sources = SourceDataset.from_env()

    if not sources or len(sources) == 0:
        return jsonify(None)

    rqueue = breg_harvester.queue.get_queue()

    store_kwargs = {
        "query_endpoint": current_app.config.get("SPARQL_ENDPOINT"),
        "update_endpoint": current_app.config.get("SPARQL_UPDATE_ENDPOINT"),
        "sparql_user": current_app.config.get("SPARQL_USER"),
        "sparql_pass": current_app.config.get("SPARQL_PASS")
    }

    if current_app.config.get("VALIDATOR_DISABLED"):
        validator = DummyValidator()
    else:
        validator = APIValidator()

    graph_uri = current_app.config.get("GRAPH_URI")

    harvest_kwargs = {
        "sources": sources,
        "store_kwargs": store_kwargs,
        "validator": validator,
        "graph_uri": graph_uri
    }

    _logger.info("Enqueuing harvest:\n%s", pprint.pformat(harvest_kwargs))

    result_ttl = current_app.config.get("RESULT_TTL")

    job = rqueue.enqueue(
        run_harvest,
        result_ttl=result_ttl,
        kwargs=harvest_kwargs)

    return breg_harvester.utils.job_to_json(job)


@blueprint.route("/<job_id>", methods=["GET"])
def get_harvest_job(job_id):
    rqueue = breg_harvester.queue.get_queue()
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
    rqueue = breg_harvester.queue.get_queue()

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
