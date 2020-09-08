import enum


class DataTypes(enum.Enum):
    XML = "xml"
    TURTLE = "n3"
    TRIPLES = "nt"
    JSONLD = "json-ld"


def mime_for_type(data_type):
    type_map = {
        DataTypes.XML: "application/rdf+xml",
        DataTypes.TURTLE: "text/turtle",
        DataTypes.TRIPLES: "application/n-triples",
        DataTypes.JSONLD: "application/ld+json"
    }

    if data_type not in type_map:
        raise ValueError("Unknown MIME type for: {}".format(data_type))

    return type_map[data_type]


class SourceDataset:
    def __init__(self, uri, data_type):
        if data_type not in DataTypes:
            raise ValueError("Unknown type: {}".format(data_type))

        self.uri = uri
        self.data_type = data_type

    def __repr__(self):
        return "<{}> Type='{}' URI='{}'".format(
            self.__class__.__name__,
            self.data_type,
            self.uri)

    @property
    def rdflib_format(self):
        return self.data_type.value

    @property
    def mime_type(self):
        return mime_for_type(self.data_type)
