import collections
import enum
import logging
import pprint
import urllib.request

import timeout_decorator
from flask import Blueprint, current_app, jsonify, request
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import DCAT, DCTERMS, SKOS
from rdflib.plugin import PluginException

import breg_harvester.store
from breg_harvester.jobs_queue import get_redis

_logger = logging.getLogger(__name__)

BLUEPRINT_NAME = "browser"
blueprint = Blueprint(BLUEPRINT_NAME, __name__)

_FORMAT_SERIALIZE = "turtle"
_TIMEOUT_URLOPEN = 10
_TIMEOUT_PARSE = 4
_KEY_FAILED = "breg:harvester:term:failed"
_PARSE_TRY_FORMATS = ["xml", "turtle", "json-ld", "nt"]

LoadGraphResult = collections.namedtuple(
    "LoadGraphResult",
    ["graph", "cache_hit", "parsed"])


@timeout_decorator.timeout(_TIMEOUT_PARSE, use_signals=False)
def _parse_with_timeout(data, frmt):
    graph = Graph()
    graph.parse(data=data, format=frmt)
    return graph.serialize(destination=None, format=_FORMAT_SERIALIZE)


def _parse_graph(graph, term):
    url = str(term)

    _logger.debug("Opening URL '%s'", url)

    with urllib.request.urlopen(url, timeout=_TIMEOUT_URLOPEN) as fh:
        url_data = fh.read().decode("utf-8")

    for frmt in _PARSE_TRY_FORMATS:
        try:
            _logger.debug("Parsing URL '%s' as %s", url, frmt)
            parsed_data = _parse_with_timeout(data=url_data, frmt=frmt)
            _logger.debug("URL '%s' contains %s", url, frmt)
            graph.parse(data=parsed_data, format=_FORMAT_SERIALIZE)
            return
        except Exception as ex:
            _logger.debug("Error parsing '%s' as %s: %s", url, frmt, ex)

    raise Exception("Could not parse %s", term)


def _build_cache_key(term):
    return f"breg:harvester:cache:{term.n3()}"


def _set_graph_redis(graph, term, redis):
    data = graph.serialize(destination=None, format=_FORMAT_SERIALIZE)
    name = _build_cache_key(term=term)
    _logger.debug("SET %s", name)
    redis.set(name=name, value=data)


def _get_graph_redis(graph, term, redis):
    name = _build_cache_key(term=term)
    _logger.debug("GET %s", name)
    data = redis.get(name=name)
    assert data, f"Undefined key: {name}"
    graph.parse(data=data, format=_FORMAT_SERIALIZE)


def _flag_parse_failed(term, redis):
    val = term.n3()
    _logger.debug("SADD :: %s :: %s", _KEY_FAILED, val)
    redis.sadd(_KEY_FAILED, val)


def _parse_has_failed_before(term, redis):
    val = term.n3()
    res = redis.sismember(_KEY_FAILED, val)
    _logger.debug("SISMEMBER :: %s :: %s = %s", _KEY_FAILED, val, res)
    return res


def _load_graph(term, redis, write_cache=True):
    graph = Graph()
    cache_hit = False
    parsed = False

    try:
        _get_graph_redis(graph=graph, term=term, redis=redis)
        cache_hit = True
    except Exception as ex:
        _logger.debug("Error loading term (%s) from Redis: %s", term, ex)

    if not cache_hit and not _parse_has_failed_before(term=term, redis=redis):
        try:
            _parse_graph(graph=graph, term=term)
            parsed = True
        except:
            _flag_parse_failed(term=term, redis=redis)
            _logger.debug("Error parsing term (%s)", term, exc_info=True)

    if write_cache and not cache_hit and parsed:
        _set_graph_redis(graph=graph, term=term, redis=redis)

    if not cache_hit and not parsed:
        graph = None

    res = LoadGraphResult(graph=graph, cache_hit=cache_hit, parsed=parsed)

    _logger.debug("Load result for term %s: %s", term, res)

    return res


def _term_to_dict(term, redis, extended=True, label_lang="en"):
    ret = {
        "n3": term.n3(),
        "class": term.__class__.__name__
    }

    if not extended or term.__class__ is not URIRef:
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


def _query_to_dicts(graph_query, idx):
    store = breg_harvester.store.get_sparql_store()
    identifier = current_app.config.get("GRAPH_URI")
    graph = Graph(store, identifier=identifier)
    qres = graph.query(graph_query)
    terms = set(item[idx] for item in qres)
    extended = bool(request.args.get("ext", False))
    redis = get_redis()

    return [
        _term_to_dict(term, redis=redis, extended=extended)
        for term in terms
    ]


@blueprint.route("/catalog/taxonomy", methods=["GET"])
def get_catalog_taxonomies():
    graph_query = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX dcat: <http://www.w3.org/ns/dcat#>
        SELECT ?subject ?predicate ?object
        WHERE {
            ?subject rdf:type dcat:Catalog .
            ?subject dcat:themeTaxonomy ?object .
        } LIMIT 50
        """

    return jsonify(_query_to_dicts(graph_query, idx=2))


@blueprint.route("/catalog/location", methods=["GET"])
def get_catalog_locations():
    graph_query = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX dcat: <http://www.w3.org/ns/dcat#>
        PREFIX dct: <http://purl.org/dc/terms/>
        SELECT ?subject ?predicate ?object
        WHERE {
            ?subject rdf:type dcat:Catalog .
            ?subject dct:spatial ?object .
        } LIMIT 50
        """

    return jsonify(_query_to_dicts(graph_query, idx=2))


@blueprint.route("/catalog/language", methods=["GET"])
def get_catalog_languages():
    graph_query = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX dcat: <http://www.w3.org/ns/dcat#>
        PREFIX dct: <http://purl.org/dc/terms/>
        SELECT ?subject ?predicate ?object
        WHERE {
            ?subject rdf:type dcat:Catalog .
            ?subject dct:LinguisticSystem ?object .
        } LIMIT 50
        """

    return jsonify(_query_to_dicts(graph_query, idx=2))


@blueprint.route("/dataset/theme", methods=["GET"])
def get_dataset_themes():
    graph_query = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX dcat: <http://www.w3.org/ns/dcat#>
        SELECT ?subject ?predicate ?object
        WHERE {
            ?subject rdf:type dcat:Dataset .
            ?subject dcat:theme ?object .
        } LIMIT 50
        """

    return jsonify(_query_to_dicts(graph_query, idx=2))


@blueprint.route("/catalog/publisher/type", methods=["GET"])
def get_catalog_publisher_types():
    graph_query = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX dcat: <http://www.w3.org/ns/dcat#>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX dct: <http://purl.org/dc/terms/>
        SELECT ?catalog ?publisher ?publisherType
        WHERE {
            ?catalog rdf:type dcat:Catalog .
            ?catalog dct:publisher ?publisher .
            ?publisher dct:type ?publisherType .
        } LIMIT 50
        """

    return jsonify(_query_to_dicts(graph_query, idx=2))


class FilterKeys(enum.Enum):
    CATALOG = "catalog"
    DATASET = "dataset"
    THEME_TAXONOMY = "themeTaxonomy"
    LANGUAGE = "language"
    THEME = "theme"
    PUBLISHER = "publisher"
    PUBLISHER_TYPE = "publisherType"
    LOCATION = "location"


def _get_datasets(graph, uris):
    graph_query = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX dcat: <http://www.w3.org/ns/dcat#>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX dct: <http://purl.org/dc/terms/>
        SELECT 
            ?catalog 
            ?dataset 
            ?description 
            ?identifier 
            ?title 
            ?distribution 
            ?distributionURL 
            ?distributionType 
            ?datasetSpatial 
            ?theme
        WHERE {{
            ?catalog rdf:type dcat:Catalog .
            ?dataset rdf:type dcat:Dataset . 
            ?catalog dcat:dataset ?dataset .
            ?dataset dct:description ?description .
            ?dataset dct:identifier ?identifier .
            ?dataset dct:title ?title .
            ?dataset dcat:distribution ?distribution . 
            ?distribution dcat:accessURL ?distributionURL .
            ?distribution dcat:mediaType ?distributionType . 
            ?dataset dct:spatial ?datasetSpatial . 
            ?dataset dcat:theme ?theme .
            FILTER (?dataset IN ({}))
        }}
        """.format(", ".join(uris))

    _logger.debug("Retrieving datasets:\n%s", graph_query)

    qres = graph.query(graph_query)

    return [{
        "catalog_uri": item[0].n3(),
        "uri": item[1].n3(),
        "description": item[2],
        "identifier": item[3],
        "title": item[4],
        "distribution_uri": item[5].n3(),
        "distribution_access_url": item[6].n3(),
        "distribution_type": item[7].n3(),
        "location": item[8].n3(),
        "theme": item[9].n3()
    } for item in qres]


@blueprint.route("/dataset/search", methods=["POST"])
def search_datasets():
    body = request.get_json()
    limit = int(body.get("limit", 200))

    filter_keys = [
        FilterKeys.CATALOG,
        FilterKeys.DATASET,
        FilterKeys.THEME_TAXONOMY,
        FilterKeys.LANGUAGE,
        FilterKeys.THEME,
        FilterKeys.PUBLISHER,
        FilterKeys.PUBLISHER_TYPE,
        FilterKeys.LOCATION
    ]

    select = " ".join([f"?{item.value}" for item in filter_keys])

    filter_args = {
        key: val for key, val in body.get("filters", {}).items()
        if key in (item.value for item in filter_keys)
    }

    filter_items = [
        "?{} IN ({})".format(filter_key, ", \n".join(values))
        for filter_key, values in filter_args.items()
    ]

    query_filter = " && ".join(filter_items)
    query_filter = "FILTER ({})".format(query_filter) if query_filter else ""

    graph_patterns = [
        f"?{FilterKeys.CATALOG.value} rdf:type dcat:Catalog",
        f"?{FilterKeys.DATASET.value} rdf:type dcat:Dataset",
        f"?{FilterKeys.CATALOG.value} dcat:dataset ?{FilterKeys.DATASET.value}",
        f"?{FilterKeys.CATALOG.value} dcat:themeTaxonomy ?{FilterKeys.THEME_TAXONOMY.value}",
        f"?{FilterKeys.CATALOG.value} dct:LinguisticSystem ?{FilterKeys.LANGUAGE.value}",
        f"?{FilterKeys.DATASET.value} dcat:theme ?{FilterKeys.THEME.value}",
        f"?{FilterKeys.CATALOG.value} dct:publisher ?{FilterKeys.PUBLISHER.value}",
        f"?{FilterKeys.PUBLISHER.value} dct:type ?{FilterKeys.PUBLISHER_TYPE.value}",
        f"?{FilterKeys.CATALOG.value} dct:spatial ?{FilterKeys.LOCATION.value}"
    ]

    graph_patterns = [f"{item} ." for item in graph_patterns]
    where = "\n".join(graph_patterns)

    search_query = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX dcat: <http://www.w3.org/ns/dcat#>
        PREFIX dct: <http://purl.org/dc/terms/>
        SELECT {select}
        WHERE {{
            {where}
            {filter}
        }} 
        LIMIT {limit}
        """.format(
        select=select,
        where=where,
        limit=limit,
        filter=query_filter)

    _logger.debug("Dataset search query:\n%s", search_query)

    store = breg_harvester.store.get_sparql_store()
    identifier = current_app.config.get("GRAPH_URI")
    graph = Graph(store, identifier=identifier)
    search_res = graph.query(search_query)

    idx_dataset = next(
        idx for idx, val in enumerate(filter_keys)
        if val is FilterKeys.DATASET)

    uris = list(set(item[idx_dataset].n3() for item in search_res))

    return jsonify({"datasets": _get_datasets(graph, uris)})
