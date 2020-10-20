"""
Attribution to:
https://edmondchuc.com/rdflib-sparqlupdatestore-5-0-0/
"""

import logging

from flask import current_app
from rdflib import BNode
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from requests.auth import HTTPDigestAuth

_logger = logging.getLogger(__name__)

_MIME_SPARQL_UPDATE = "application/sparql-update"


def _node_to_sparql(node):
    """Function to map BNodes to a representation that is allowed by the SPARQLStore."""

    if isinstance(node, BNode):
        return "<bnode:b%s>" % node

    return node.n3()


def get_sparql_store(query_endpoint=None, update_endpoint=None, sparql_user=None, sparql_pass=None):
    if not query_endpoint:
        query_endpoint = current_app.config.get("SPARQL_ENDPOINT")

    if not update_endpoint:
        update_endpoint = current_app.config.get("SPARQL_UPDATE_ENDPOINT")

    if not sparql_user:
        sparql_user = current_app.config.get("SPARQL_USER")

    if not sparql_pass:
        sparql_pass = current_app.config.get("SPARQL_PASS")

    auth = HTTPDigestAuth(sparql_user, sparql_pass)

    store = SPARQLUpdateStore(
        queryEndpoint=query_endpoint,
        update_endpoint=update_endpoint,
        auth=auth,
        context_aware=True,
        postAsEncoded=False,
        node_to_sparql=_node_to_sparql)

    store.method = "POST"
    store.formula_aware = True

    return store


def set_store_header_update(store):
    """Call this function before any `Graph.add()` 
    calls to set the appropriate request headers."""

    if "headers" not in store.kwargs:
        store.kwargs.update({"headers": {}})

    store.kwargs['headers'].update({
        "content-type": _MIME_SPARQL_UPDATE
    })

    _logger.debug(
        "Updated store (%s) content-type: %s",
        store, _MIME_SPARQL_UPDATE)


def set_store_header_read(store):
    """Call this function before any `Graph.triples()` 
    calls to set the appropriate request headers."""

    if "headers" not in store.kwargs:
        store.kwargs.update({"headers": {}})

    store.kwargs["headers"].pop("content-type", None)

    _logger.debug("Cleared store (%s) content-type", store)
