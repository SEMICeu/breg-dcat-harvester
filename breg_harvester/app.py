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

ENV_LOG_LEVEL = "BREG_LOG_LEVEL"
ENV_REDIS = "BREG_REDIS"
ENV_STORE = "BREG_TRIPLE_STORE"
ENV_GRAPH_URI = "BREG_GRAPH_URI"
ENV_SECRET = "BREG_SECRET_KEY"
ENV_PORT = "BREG_PORT"
ENV_SPAWN = "BREG_SERVER_SPAWN"

DEFAULT_SECRET = "secret"
DEFAULT_REDIS = "redis://redis"
DEFAULT_STORE = "http://virtuoso:8890/sparql"
DEFAULT_GRAPH_URI = "http://localhost/pilot"
DEFAULT_PORT = 5000
DEFAULT_SPAWN = 5
DEFAULT_BIND_HOST = "0.0.0.0"

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
    store_url = os.getenv(ENV_STORE, DEFAULT_STORE)
    graph_uri = os.getenv(ENV_GRAPH_URI, DEFAULT_GRAPH_URI)

    conf_mapping = {
        "SECRET_KEY": secret_key,
        "REDIS_URL": redis_url,
        "TRIPLE_STORE_URL": store_url,
        "GRAPH_URI": graph_uri
    }

    _logger.debug("Flask configuration:\n%s", pprint.pformat(conf_mapping))

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
        instance_relative_config=True)

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
