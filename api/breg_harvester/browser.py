import collections
import logging
import pprint

from flask import Blueprint, current_app, jsonify, request
from rdflib import Graph
from rdflib.namespace import DCAT, DCTERMS, SKOS
from rdflib.plugin import PluginException

import breg_harvester.store
from breg_harvester.jobs_queue import get_redis

_logger = logging.getLogger(__name__)

BLUEPRINT_NAME = "browser"
blueprint = Blueprint(BLUEPRINT_NAME, __name__)

_FORMAT_REDIS = "xml"

LoadGraphResult = collections.namedtuple(
    "LoadGraphResult",
    ["graph", "cache_hit", "parsed"])


def _parse_graph(graph, term):
    formats = [None, "xml", "turtle", "nt", "json-ld"]

    for frmt in formats:
        try:
            graph.parse(term, format=frmt)
            return
        except (PluginException, SyntaxError):
            pass


def _build_redis_key(term):
    return f"breg:harvester:cache:{term.n3()}"


def _set_graph_redis(graph, term, redis):
    data = graph.serialize(destination=None, format=_FORMAT_REDIS)
    name = _build_redis_key(term=term)
    _logger.debug("SET %s", name)
    redis.set(name=name, value=data)


def _get_graph_redis(graph, term, redis):
    name = _build_redis_key(term=term)
    _logger.debug("GET %s", name)
    data = redis.get(name=name)
    assert data, f"Undefined key: {name}"
    graph.parse(data=data, format=_FORMAT_REDIS)


def _load_graph(term, redis, write_cache=True):
    graph = Graph()
    cache_hit = False
    parsed = False

    try:
        _get_graph_redis(graph=graph, term=term, redis=redis)
        cache_hit = True
    except:
        _logger.debug(
            "Error loading term (%s) from Redis",
            term, exc_info=True)

    if not cache_hit:
        try:
            _parse_graph(graph=graph, term=term)
            parsed = True
        except:
            _logger.debug(
                "Error parsing term (%s)",
                term, exc_info=True)

    if write_cache and not cache_hit and parsed:
        _set_graph_redis(graph=graph, term=term, redis=redis)

    if not cache_hit and not parsed:
        graph = None

    res = LoadGraphResult(graph=graph, cache_hit=cache_hit, parsed=parsed)

    _logger.debug("Load result for term %s: %s", term, res)

    return res


def _term_to_dict(term, redis, extended=True, label_lang="en"):
    ret = {"n3": term.n3()}

    if not extended:
        return ret

    load_res = _load_graph(term=term, redis=redis, write_cache=True)

    if not load_res.graph:
        return ret

    labels = load_res.graph.preferredLabel(subject=term, lang=label_lang)
    label = labels[0][1] if len(labels) > 0 else None
    label_prop = labels[0][0] if len(labels) > 0 else None

    ret.update({
        "label": label,
        "label_prop": label_prop
    })

    return ret


@blueprint.route("/catalog/taxonomy", methods=["GET"])
def get_catalog_taxonomies():
    store = breg_harvester.store.get_sparql_store()
    graph = Graph(store, identifier=current_app.config.get("GRAPH_URI"))

    qres = graph.query("""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX dcat: <http://www.w3.org/ns/dcat#>
        SELECT ?subject ?predicate ?object
        WHERE {
            ?subject rdf:type dcat:Catalog .
            ?subject dcat:themeTaxonomy ?object .
        } LIMIT 30
        """)

    terms = set(item[2] for item in qres)
    extended = bool(request.args.get("ext"))
    redis = get_redis()

    return jsonify([
        _term_to_dict(term, redis=redis, extended=extended)
        for term in terms
    ])


@blueprint.route("/dataset/theme", methods=["GET"])
def get_dataset_themes():
    store = breg_harvester.store.get_sparql_store()
    graph = Graph(store, identifier=current_app.config.get("GRAPH_URI"))

    qres = graph.query("""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX dcat: <http://www.w3.org/ns/dcat#>
        SELECT ?subject ?predicate ?object
        WHERE {
            ?subject rdf:type dcat:Dataset .
            ?subject dcat:theme ?object .
        } LIMIT 30
        """)

    terms = set(item[2] for item in qres)
    extended = bool(request.args.get("ext"))
    redis = get_redis()

    return jsonify([
        _term_to_dict(term, redis=redis, extended=extended)
        for term in terms
    ])
