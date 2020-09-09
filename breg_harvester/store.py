"""
Attribution to:
https://edmondchuc.com/rdflib-sparqlupdatestore-5-0-0/
"""

import logging

from flask import current_app
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from requests.auth import HTTPDigestAuth

_logger = logging.getLogger(__name__)

_MIME_SPARQL_UPDATE = "application/sparql-update"


def get_sparql_store(query_endpoint=None, update_endpoint=None, auth=None):
    if not query_endpoint:
        query_endpoint = current_app.config.get("SPARQL_ENDPOINT")

    if not update_endpoint:
        update_endpoint = current_app.config.get("SPARQL_UPDATE_ENDPOINT")

    if not auth:
        user = current_app.config.get("SPARQL_USER")
        pasw = current_app.config.get("SPARQL_PASS")
        auth = HTTPDigestAuth(user, pasw)

    store = SPARQLUpdateStore(
        queryEndpoint=query_endpoint,
        update_endpoint=update_endpoint,
        auth=auth,
        context_aware=True,
        postAsEncoded=False)

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
