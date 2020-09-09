import json
import logging
import pprint

import requests
from flask import Blueprint, current_app, g
from rdflib import Graph
from SPARQLWrapper import SPARQLWrapper

import breg_harvester.store
from breg_harvester.models import DataTypes, mime_for_type

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


def run_harvest(sources, store=None, validator=None, graph_uri=None):
    if not store:
        store = breg_harvester.store.get_sparql_store()
        _logger.debug("Using default store: %s", store)

    if not validator:
        validator = APIValidator()
        _logger.debug("Using default validator: %s", validator)

    if not graph_uri:
        graph_uri = current_app.config.get("GRAPH_URI")
        _logger.debug("Using default graph URI: %s", graph_uri)

    store_graph = Graph(store, identifier=graph_uri)

    _logger.debug("Original sources:\n%s", pprint.pformat(sources))

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

    _logger.debug("Number of triples harvested: %s", len(store_graph))

    store_graph.close()


@blueprint.route("/", methods=["GET"])
def get_harvest():
    return {}


@blueprint.route("/", methods=["POST"])
def create_harvest():
    return {}
