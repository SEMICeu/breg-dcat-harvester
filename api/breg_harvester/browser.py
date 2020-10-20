import logging
import pprint

from flask import Blueprint, current_app, jsonify, request
from rdflib import Graph
from rdflib.namespace import DCAT, DCTERMS, SKOS
from rdflib.plugin import PluginException

import breg_harvester.store

_logger = logging.getLogger(__name__)

BLUEPRINT_NAME = "browser"
blueprint = Blueprint(BLUEPRINT_NAME, __name__)

_FORMATS = [None, "xml", "turtle", "nt", "json-ld"]


def _graph_parse(graph, term, formats=None):
    formats = formats or _FORMATS

    for frmt in formats:
        try:
            graph.parse(term, format=frmt)
            return
        except (PluginException, SyntaxError):
            pass


def _term_to_dict(term, extended=True, label_lang="en"):
    ret = {"n3": term.n3()}

    if not extended:
        return ret

    try:
        graph = Graph()
        _graph_parse(graph=graph, term=term)
        labels = graph.preferredLabel(subject=term, lang=label_lang)
        pref_label = labels[0] if len(labels) > 0 else None

        ret.update({
            "label": pref_label[1] if pref_label else None,
            "label_prop": pref_label[0] if pref_label else None
        })
    except Exception as ex:
        _logger.info("Error parsing term (%s): %s", term, ex)

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

    return jsonify([_term_to_dict(term, extended=extended) for term in terms])


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

    return jsonify([_term_to_dict(term, extended=extended) for term in terms])
