import json
import logging
import os
import pprint

from flask import Flask, current_app, jsonify
from flask_cors import CORS
from gevent.pywsgi import WSGIServer
from werkzeug.exceptions import HTTPException

import breg_harvester.harvest
import breg_harvester.jobs_queue
import breg_harvester.scheduler
from breg_harvester.config import DEFAULT_ENV_CONFIG, AppConfig, EnvConfig

STATIC_FOLDER = "spa"
STATIC_URL_PATH = ""
BIND_HOST = "0.0.0.0"
PREFIX_HARVEST = "/api/harvest"
PREFIX_SCHEDULER = "/api/scheduler"

_logger = logging.getLogger(__name__)


def _config_from_env(app):
    secret_key = os.getenv(EnvConfig.SECRET.value, None)

    if not secret_key:
        _logger.warning(
            "Undefined secret $%s: Using default",
            DEFAULT_ENV_CONFIG[EnvConfig.SECRET])

        secret_key = DEFAULT_ENV_CONFIG[EnvConfig.SECRET]

    redis_url = os.getenv(
        EnvConfig.REDIS.value,
        DEFAULT_ENV_CONFIG[EnvConfig.REDIS])

    sparql = os.getenv(
        EnvConfig.SPARQL.value,
        DEFAULT_ENV_CONFIG[EnvConfig.SPARQL])

    sparql_udpate = os.getenv(
        EnvConfig.SPARQL_UPDATE.value,
        DEFAULT_ENV_CONFIG[EnvConfig.SPARQL_UPDATE])

    graph_uri = os.getenv(
        EnvConfig.GRAPH_URI.value,
        DEFAULT_ENV_CONFIG[EnvConfig.GRAPH_URI])

    sparql_user = os.getenv(
        EnvConfig.SPARQL_USER.value,
        DEFAULT_ENV_CONFIG[EnvConfig.SPARQL_USER])

    sparql_pass = os.getenv(
        EnvConfig.SPARQL_PASS.value,
        DEFAULT_ENV_CONFIG[EnvConfig.SPARQL_PASS])

    validator_disabled = bool(os.getenv(
        EnvConfig.VALIDATOR_DISABLED.value,
        DEFAULT_ENV_CONFIG[EnvConfig.VALIDATOR_DISABLED]))

    result_ttl = int(os.getenv(
        EnvConfig.RESULT_TTL.value,
        DEFAULT_ENV_CONFIG[EnvConfig.RESULT_TTL]))

    conf_mapping = {
        AppConfig.SECRET_KEY.value: secret_key,
        AppConfig.REDIS_URL.value: redis_url,
        AppConfig.SPARQL_ENDPOINT.value: sparql,
        AppConfig.SPARQL_UPDATE_ENDPOINT.value: sparql_udpate,
        AppConfig.GRAPH_URI.value: graph_uri,
        AppConfig.SPARQL_USER.value: sparql_user,
        AppConfig.SPARQL_PASS.value: sparql_pass,
        AppConfig.VALIDATOR_DISABLED.value: validator_disabled,
        AppConfig.RESULT_TTL.value: result_ttl
    }

    _logger.info("Flask configuration:\n%s", pprint.pformat(conf_mapping))

    app.config.from_mapping(**conf_mapping)


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

    _config_from_env(app)

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

    breg_harvester.jobs_queue.init_app_redis(app)

    app.add_url_rule("/", view_func=catch_all, defaults={"path": ""})
    app.add_url_rule("/<path:path>", view_func=catch_all)

    app.register_error_handler(Exception, handle_exception)

    CORS(app)

    return app


def run_wsgi_server():
    port = int(os.getenv(
        EnvConfig.PORT.value,
        DEFAULT_ENV_CONFIG[EnvConfig.PORT]))

    spawn = int(os.getenv(
        EnvConfig.SPAWN.value,
        DEFAULT_ENV_CONFIG[EnvConfig.SPAWN]))

    app = create_app()

    _logger.info(
        "Starting server on port %s with a pool of %s workers",
        port, spawn)

    http_server = WSGIServer(
        (BIND_HOST, port),
        application=app,
        log=_logger,
        error_log=_logger,
        spawn=spawn)

    http_server.serve_forever()
