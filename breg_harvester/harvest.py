from flask import Blueprint, g

BLUEPRINT_NAME = "harvest"
blueprint = Blueprint(BLUEPRINT_NAME, __name__)


@blueprint.route("/", methods=["GET"])
def get_harvest():
    return {}


@blueprint.route("/", methods=["POST"])
def create_harvest():
    return {}
