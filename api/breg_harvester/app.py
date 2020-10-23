import json
import logging
import os
import pprint

from flask import Flask, current_app, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException, NotFound

import breg_harvester.browser
import breg_harvester.harvest
import breg_harvester.jobs_queue
import breg_harvester.scheduler
from breg_harvester.config import AppConfig, app_config_from_env

STATIC_FOLDER = "spa"
STATIC_URL_PATH = ""
BIND_HOST = "0.0.0.0"
PREFIX_HARVEST = "/api/harvest"
PREFIX_SCHEDULER = "/api/scheduler"
PREFIX_BROWSER = "/api/browser"

_logger = logging.getLogger(__name__)


def jsonify_http_exception(err):
    response = err.get_response()

    response.data = json.dumps({
        "code": err.code,
        "name": err.name,
        "description": err.description,
    })

    response.content_type = "application/json"

    return response


def handle_exception(err):
    if isinstance(err, NotFound):
        return current_app.send_static_file("index.html")

    if isinstance(err, HTTPException):
        return jsonify_http_exception(err)

    _logger.warning("Request error: %s", repr(err))

    code = 500

    data = {
        "code": code,
        "name": err.__class__.__name__,
        "description": str(err)
    }

    return jsonify(data), code


def catch_all(path):
    return current_app.send_static_file("index.html")


def create_app(test_config=None, with_scheduler=True):
    app = Flask(
        __name__,
        instance_relative_config=True,
        static_folder=STATIC_FOLDER,
        static_url_path=STATIC_URL_PATH)

    config_map = app_config_from_env()

    secure_config_map = config_map.copy()
    secure_config_map.pop(AppConfig.SECRET_KEY.value)

    _logger.info(
        "Flask app configuration:\n%s",
        pprint.pformat(secure_config_map))

    app.config.from_mapping(**config_map)

    if test_config is not None:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    if with_scheduler:
        breg_harvester.scheduler.init_scheduler(app)

    app.register_blueprint(
        breg_harvester.harvest.blueprint,
        url_prefix=PREFIX_HARVEST)

    app.register_blueprint(
        breg_harvester.scheduler.blueprint,
        url_prefix=PREFIX_SCHEDULER)

    app.register_blueprint(
        breg_harvester.browser.blueprint,
        url_prefix=PREFIX_BROWSER)

    breg_harvester.jobs_queue.init_app_redis(app)

    app.add_url_rule("/", view_func=catch_all, defaults={"path": ""})
    app.add_url_rule("/<path:path>", view_func=catch_all)

    app.register_error_handler(Exception, handle_exception)

    CORS(app)

    return app
