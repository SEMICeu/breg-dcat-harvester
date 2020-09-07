import os
import pprint

from pyshacl import validate
from rdflib import Graph

PATH_BASE = "/Users/agmangas/Documents/Projects/breg-harvester"

PATH_DATA = os.path.join(
    PATH_BASE,
    "breg_harvester/ontology/sample.xml")

PATH_SHAPES = os.path.join(
    PATH_BASE,
    "breg_harvester/ontology/BRegDCAT-AP_shacl_shapes_2.00.ttl")

PATH_MDR = os.path.join(
    PATH_BASE,
    "breg_harvester/ontology/BRegDCAT-AP_shacl_mdr-vocabularies_2.00.ttl")


def print_graph(graph):
    for s, p, o in graph:
        pprint.pprint((s, p, o))


if __name__ == "__main__":
    graph_data = Graph()
    graph_data.parse(PATH_DATA, format="xml")
    print_graph(graph_data)

    graph_shapes = Graph()
    graph_shapes.parse(PATH_SHAPES, format="turtle")

    graph_mdr = Graph()
    graph_mdr.parse(PATH_MDR, format="turtle")

    res_shapes = validate(
        graph_data,
        shacl_graph=graph_shapes,
        advanced=True,
        debug=True,
        inference="both")

    pprint.pprint(res_shapes)

    res_mdr = validate(
        graph_data,
        shacl_graph=graph_mdr,
        advanced=True,
        debug=True,
        inference="both")

    pprint.pprint(res_mdr)
