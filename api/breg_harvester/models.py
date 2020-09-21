import enum
import json
import logging
import os

_logger = logging.getLogger(__name__)


class DataTypes(enum.Enum):
    XML = "xml"
    TURTLE = "turtle"
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


def _find_enum(enum_cls, item_val):
    try:
        return next(item for item in enum_cls if item.value == item_val)
    except StopIteration:
        raise ValueError(f"'{item_val}' is not in enum {list(enum_cls)}")


class SourceDataset:
    ENV_SOURCES = "HARVESTER_SOURCES"

    @classmethod
    def from_env(cls):
        sources_str = os.getenv(cls.ENV_SOURCES)

        if not sources_str:
            return None

        return [
            SourceDataset(uri, _find_enum(DataTypes, type_val))
            for uri, type_val in json.loads(sources_str)
        ]

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

    def to_dict(self):
        return {
            "uri": self.uri,
            "data_type": self.data_type.value,
            "mime": self.mime_type,
            "format": self.rdflib_format
        }
