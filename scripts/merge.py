"""
Attribution to:
https://edmondchuc.com/rdflib-sparqlupdatestore-5-0-0/
"""

import os
import pprint

from rdflib import Graph
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from requests.auth import HTTPDigestAuth

GRAPH_URI = "http://test.com/"
SPARQL_ENDPOINT = "http://localhost:8890/sparql"
SPARQL_UPDATE_ENDPOINT = "http://localhost:8890/sparql-auth"

AUTH_USER = "dba"
AUTH_PASS = "root"

SOURCES = [
    ("http://localhost:8080/sample-01.xml", "xml"),
    ("http://localhost:8080/sample-02.ttl", "n3")
]


def set_store_header_update(store):
    """Call this function before any `Graph.add()` 
    calls to set the appropriate request headers."""

    if "headers" not in store.kwargs:
        store.kwargs.update({"headers": {}})

    store.kwargs['headers'].update({
        "content-type": "application/sparql-update"
    })


def set_store_header_read(store):
    """Call this function before any `Graph.triples()` 
    calls to set the appropriate request headers."""

    if "headers" not in store.kwargs:
        store.kwargs.update({"headers": {}})

    store.kwargs["headers"].pop("content-type", None)


if __name__ == "__main__":
    store = SPARQLUpdateStore(
        queryEndpoint=SPARQL_ENDPOINT,
        update_endpoint=SPARQL_UPDATE_ENDPOINT,
        auth=HTTPDigestAuth(AUTH_USER, AUTH_PASS),
        context_aware=True,
        postAsEncoded=False)

    store.method = "POST"
    store.formula_aware = True

    store_graph = Graph(store=store, identifier=GRAPH_URI)

    set_store_header_update(store)

    for data_url, frmt in SOURCES:
        print("Parsing ({}): {}".format(frmt, data_url))
        store_graph.parse(data_url, format=frmt)

    set_store_header_read(store)

    print("Updated {} triples".format(len(store_graph)))

    for triple in store_graph.triples((None, None, None)):
        pprint.pprint(triple)

    store_graph.close()
