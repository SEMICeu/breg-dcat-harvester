import json
import logging
import pprint

import rdflib
import requests
from flask import current_app
from rdflib.namespace import SH

from breg_harvester.models import DataTypes, mime_for_type

_logger = logging.getLogger(__name__)

URL_API_ANY = "https://www.itb.ec.europa.eu/shacl/any/api/validate"
URL_API_BREG = "https://www.itb.ec.europa.eu/shacl/bregdcat-ap/api/validate"

URL_SHACL_MDR = (
    "https://joinup.ec.europa.eu/sites/default/files/distribution/access_url/2020-07/"
    "404077ab-f8aa-4580-a436-741ae42e0c3a/"
    "BRegDCAT-AP_shacl_mdr-vocabularies_2.00.ttl"
)

URL_SHACL_SHAPES = (
    "https://joinup.ec.europa.eu/sites/default/files/distribution/access_url/2020-07/"
    "24180c3dc-b405-49c8-91f0-8d3a7fe51e9e/"
    "BRegDCAT-AP_shacl_shapes_2.00.ttl"
)

VALIDATION_TYPE_ANY = "any"
VALIDATION_TYPE_LATEST = "latest"
EMBEDDING_METHOD_URL = "URL"


def validation_report_conforms(data, strict):
    grph = rdflib.Graph()
    grph.parse(data=data)

    _logger.debug(
        "Checking SHACL validation report:\n%s",
        pprint.pformat(list(grph.triples((None, None, None)))))

    triples_conforms = grph.triples((None, SH.conforms, rdflib.Literal(True)))
    conforms = len(list(triples_conforms)) > 0

    if conforms:
        return True
    elif not conforms and strict:
        return False

    triples_violation = grph.triples((None, SH.resultSeverity, SH.Violation))
    has_violations = len(list(triples_violation)) > 0

    return not has_violations


def _request_validation(url_api, body, strict):
    try:
        _logger.debug("Request validation (%s):\n%s", url_api, body)
        res = requests.post(url_api, json=body)
        return validation_report_conforms(data=res.text, strict=strict)
    except:
        _logger.warning("Error on validation API request", exc_info=True)
        return False


class GenericAPIValidator:
    def __init__(self, url_api=URL_API_ANY, external_rules=None):
        self.url_api = url_api

        default_rules = [
            (URL_SHACL_MDR, DataTypes.TURTLE),
            (URL_SHACL_SHAPES, DataTypes.TURTLE)
        ]

        self.external_rules = external_rules if external_rules else default_rules

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
            "reportSyntax": mime_for_type(DataTypes.XML),
            "externalRules": external_rules
        }

    def validate(self, source, strict=False):
        body = self.build_source_body(
            source=source,
            external_rules=self.external_rules)

        return _request_validation(self.url_api, body, strict)


class BRegAPIValidator:
    def __init__(self, url_api=URL_API_BREG):
        self.url_api = url_api

    def build_source_body(self, source):
        return {
            "contentSyntax": source.mime_type,
            "contentToValidate": source.uri,
            "embeddingMethod": EMBEDDING_METHOD_URL,
            "validationType": VALIDATION_TYPE_LATEST,
            "reportSyntax": mime_for_type(DataTypes.XML)
        }

    def validate(self, source, strict=False):
        body = self.build_source_body(source=source)
        return _request_validation(self.url_api, body, strict)


class DummyValidator:
    def validate(self, *args, **kwargs):
        return True


def get_validator(app_config=None):
    app_config = app_config if app_config else current_app.config

    try:
        is_disabled = bool(app_config.get("VALIDATOR_DISABLED"))
    except Exception as ex:
        _logger.info("Error checking current app config: %s", ex)
        is_disabled = False

    if is_disabled:
        _logger.info("Validator disabled: Using %s", DummyValidator)
        return DummyValidator()

    return BRegAPIValidator()
