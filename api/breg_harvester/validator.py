import json
import logging
import pprint

import requests

from breg_harvester.models import DataTypes, mime_for_type

_logger = logging.getLogger(__name__)

URL_API_ANY = "https://www.itb.ec.europa.eu/shacl/any/api/validate"

URL_SHACL_MDR = (
    "https://raw.githubusercontent.com/agmangas/breg-dcat-harvester/"
    "bc3b337c9304c854aef46d9e552e6a890a9deddf/api/breg_harvester/ontology/"
    "BRegDCAT-AP_shacl_mdr-vocabularies_2.00.ttl"
)

URL_SHACL_SHAPES = (
    "https://raw.githubusercontent.com/agmangas/breg-dcat-harvester/"
    "bc3b337c9304c854aef46d9e552e6a890a9deddf/api/breg_harvester/ontology/"
    "BRegDCAT-AP_shacl_shapes_2.00.ttl"
)

VALIDATION_TYPE_ANY = "any"
EMBEDDING_METHOD_URL = "URL"
SHACL_RESULT_SEVERITY = "sh:resultSeverity"
SHACL_SEVERITY_VIOLATION = "sh:Violation"
SHACL_CONFORMS = "sh:conforms"
JSONLD_GRAPH = "@graph"


def jsonld_report_conforms(report, strict):
    _logger.debug(
        "Processing SHACL JSON-LD report (strict=%s):\n%s",
        strict, pprint.pformat(report))

    if JSONLD_GRAPH not in report and SHACL_CONFORMS in report:
        return report[SHACL_CONFORMS]
    elif JSONLD_GRAPH not in report:
        _logger.warning("Key '%s' not found in JSON-LD report", JSONLD_GRAPH)
        return True

    root = report[JSONLD_GRAPH]
    conforms = any(item.get(SHACL_CONFORMS, False) for item in root)

    if conforms:
        return True
    elif strict:
        return False

    any_violation = any(
        item.get(SHACL_RESULT_SEVERITY) == SHACL_SEVERITY_VIOLATION
        for item in root)

    return not any_violation


class ITBAnyValidator:
    def __init__(self, url_api=URL_API_ANY):
        self.url_api = url_api

    def build_source_body(self, source, external_rules):
        external_rules = [
            {
                "ruleSet": rule_url,
                "ruleSyntax": mime_for_type(rule_type),
                "embeddingMethod": EMBEDDING_METHOD_URL
            }
            for rule_url, rule_type in external_rules
        ]

        return {
            "contentSyntax": source.mime_type,
            "contentToValidate": source.uri,
            "embeddingMethod": EMBEDDING_METHOD_URL,
            "validationType": VALIDATION_TYPE_ANY,
            "reportSyntax": mime_for_type(DataTypes.JSONLD),
            "externalRules": external_rules
        }

    def validate(self, source, strict=False, external_rules=None):
        default_rules = [
            (URL_SHACL_MDR, DataTypes.TURTLE),
            (URL_SHACL_SHAPES, DataTypes.TURTLE)
        ]

        external_rules = external_rules if external_rules else default_rules
        body = self.build_source_body(source, external_rules)

        try:
            _logger.debug("Request validation (%s): %s", self.url_api, body)
            res = requests.post(self.url_api, json=body)
            report = json.loads(res.text)
            return jsonld_report_conforms(report=report, strict=strict)
        except:
            _logger.warning("Error on validator API request", exc_info=True)
            return False


class DummyValidator:
    def validate(self, *args, **kwargs):
        _logger.info("Using validator: %s", self.__class__)
        return True
