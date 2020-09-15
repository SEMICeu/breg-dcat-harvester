import json
import logging
import os
import pprint

import coloredlogs
from flask import Flask, jsonify
from flask_cors import CORS
from gevent.pywsgi import WSGIServer
from werkzeug.exceptions import HTTPException

import breg_harvester.harvest
import breg_harvester.queue

STATIC_FOLDER = "spa"
STATIC_URL_PATH = ""

ENV_LOG_LEVEL = "HARVESTER_LOG_LEVEL"
ENV_REDIS = "HARVESTER_REDIS"
ENV_SPARQL = "HARVESTER_SPARQL_ENDPOINT"
ENV_SPARQL_UPDATE = "HARVESTER_SPARQL_UPDATE_ENDPOINT"
ENV_GRAPH_URI = "HARVESTER_GRAPH_URI"
ENV_SPARQL_USER = "HARVESTER_SPARQL_USER"
ENV_SPARQL_PASS = "HARVESTER_SPARQL_PASS"
ENV_SECRET = "HARVESTER_SECRET_KEY"
ENV_PORT = "HARVESTER_PORT"
ENV_SPAWN = "HARVESTER_SERVER_SPAWN"
ENV_VALIDATOR_DISABLED = "HARVESTER_VALIDATOR_DISABLED"
ENV_RESULT_TTL = "HARVESTER_RESULT_TTL"

DEFAULT_SECRET = "secret"
DEFAULT_REDIS = "redis://redis"
DEFAULT_SPARQL = "http://virtuoso:8890/sparql"
DEFAULT_SPARQL_UPDATE = "http://virtuoso:8890/sparql-auth"
DEFAULT_GRAPH_URI = "http://fundacionctic.org/breg-harvester"
DEFAULT_SPARQL_USER = "dba"
DEFAULT_SPARQL_PASS = "dba"
DEFAULT_PORT = 5000
DEFAULT_SPAWN = 5
DEFAULT_BIND_HOST = "0.0.0.0"
DEFAULT_RESULT_TTL = 3600 * 24 * 30

PREFIX_HARVEST = "/api/harvest"

_logger = logging.getLogger(__name__)


def init_logging():
    is_prod = os.getenv("FLASK_ENV", "production") == "production"
    level_default = logging.INFO if is_prod else logging.DEBUG
    level = os.getenv(ENV_LOG_LEVEL, level_default)
    base_logger = logging.getLogger(__name__.split(".")[0])
    coloredlogs.install(level=level, logger=base_logger)


def _config_from_env(app):
    secret_key = os.getenv(ENV_SECRET, None)

    if not secret_key:
        _logger.warning("Undefined secret $%s: Using default", ENV_SECRET)
        secret_key = DEFAULT_SECRET

    redis_url = os.getenv(ENV_REDIS, DEFAULT_REDIS)
    sparql = os.getenv(ENV_SPARQL, DEFAULT_SPARQL)
    sparql_udpate = os.getenv(ENV_SPARQL_UPDATE, DEFAULT_SPARQL_UPDATE)
    graph_uri = os.getenv(ENV_GRAPH_URI, DEFAULT_GRAPH_URI)
    sparql_user = os.getenv(ENV_SPARQL_USER, DEFAULT_SPARQL_USER)
    sparql_pass = os.getenv(ENV_SPARQL_PASS, DEFAULT_SPARQL_PASS)
    validator_disabled = bool(os.getenv(ENV_VALIDATOR_DISABLED))
    result_ttl = int(os.getenv(ENV_RESULT_TTL, DEFAULT_RESULT_TTL))

    conf_mapping = {
        "SECRET_KEY": secret_key,
        "REDIS_URL": redis_url,
        "SPARQL_ENDPOINT": sparql,
        "SPARQL_UPDATE_ENDPOINT": sparql_udpate,
        "GRAPH_URI": graph_uri,
        "SPARQL_USER": sparql_user,
        "SPARQL_PASS": sparql_pass,
        "VALIDATOR_DISABLED": validator_disabled,
        "RESULT_TTL": result_ttl
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


def create_app(test_config=None):
    init_logging()

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

    app.register_blueprint(
        breg_harvester.harvest.blueprint,
        url_prefix=PREFIX_HARVEST)

    breg_harvester.queue.init_app_redis(app)

    # pylint: disable=unused-variable
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def catch_all(path):
        return app.send_static_file("index.html")

    app.register_error_handler(Exception, handle_exception)
    CORS(app)

    return app


def run_wsgi_server():
    port = int(os.getenv(ENV_PORT, DEFAULT_PORT))
    spawn = int(os.getenv(ENV_SPAWN, DEFAULT_SPAWN))

    app = create_app()

    _logger.info(
        "Starting server on port %s with a pool of %s workers",
        port, spawn)

    http_server = WSGIServer(
        (DEFAULT_BIND_HOST, port),
        application=app,
        log=_logger,
        error_log=_logger,
        spawn=spawn)

    http_server.serve_forever()
