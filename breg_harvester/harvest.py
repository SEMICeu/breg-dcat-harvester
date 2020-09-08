import json
import logging

import requests
from flask import Blueprint, g

from breg_harvester.models import DataTypes, mime_for_type

_logger = logging.getLogger(__name__)

BLUEPRINT_NAME = "harvest"
blueprint = Blueprint(BLUEPRINT_NAME, __name__)


class APIValidator:
    API_URL = "https://www.itb.ec.europa.eu/shacl/cpsv-ap/api/validate"

    @classmethod
    def build_source_body(cls, source):
        return {
            "contentSyntax": source.mime_type,
            "contentToValidate": source.uri,
            "embeddingMethod": "URL",
            "reportSyntax": mime_for_type(DataTypes.JSONLD)
        }

    def __init__(self, api_url=API_URL):
        self.api_url = api_url

    def validate(self, source):
        try:
            body = self.build_source_body(source)
            res = requests.post(self.api_url, json=body)
            res_json = json.loads(res.text)
            return res_json.get("sh:conforms", False)
        except:
            _logger.warning("Error on validator API request", exc_info=True)
            return False


@blueprint.route("/", methods=["GET"])
def get_harvest():
    return {}


@blueprint.route("/", methods=["POST"])
def create_harvest():
    return {}
