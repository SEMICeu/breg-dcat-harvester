import enum
import logging
import os

_logger = logging.getLogger(__name__)


class EnvConfig(enum.Enum):
    SECRET = "HARVESTER_SECRET_KEY"
    REDIS = "HARVESTER_REDIS"
    SPARQL = "HARVESTER_SPARQL_ENDPOINT"
    SPARQL_UPDATE = "HARVESTER_SPARQL_UPDATE_ENDPOINT"
    GRAPH_URI = "HARVESTER_GRAPH_URI"
    SPARQL_USER = "HARVESTER_SPARQL_USER"
    SPARQL_PASS = "HARVESTER_SPARQL_PASS"
    PORT = "HARVESTER_PORT"
    SPAWN = "HARVESTER_SERVER_SPAWN"
    VALIDATOR_DISABLED = "HARVESTER_VALIDATOR_DISABLED"
    RESULT_TTL = "HARVESTER_RESULT_TTL"
    SCHEDULER_JOB_ID = "HARVESTER_SCHEDULER_JOB_ID"


DEFAULT_ENV_CONFIG = {
    EnvConfig.SECRET: "secret",
    EnvConfig.REDIS: "redis://redis",
    EnvConfig.SPARQL: "http://virtuoso:8890/sparql",
    EnvConfig.SPARQL_UPDATE: "http://virtuoso:8890/sparql-auth",
    EnvConfig.GRAPH_URI: "http://fundacionctic.org/breg-harvester",
    EnvConfig.SPARQL_USER: "dba",
    EnvConfig.SPARQL_PASS: "dba",
    EnvConfig.PORT: 5000,
    EnvConfig.SPAWN: 5,
    EnvConfig.VALIDATOR_DISABLED: False,
    EnvConfig.RESULT_TTL: 3600 * 24 * 30,
    EnvConfig.SCHEDULER_JOB_ID: "harvester-scheduled-job"
}


class AppConfig(enum.Enum):
    SECRET_KEY = "SECRET_KEY"
    REDIS_URL = "REDIS_URL"
    SPARQL_ENDPOINT = "SPARQL_ENDPOINT"
    SPARQL_UPDATE_ENDPOINT = "SPARQL_UPDATE_ENDPOINT"
    GRAPH_URI = "GRAPH_URI"
    SPARQL_USER = "SPARQL_USER"
    SPARQL_PASS = "SPARQL_PASS"
    VALIDATOR_DISABLED = "VALIDATOR_DISABLED"
    RESULT_TTL = "RESULT_TTL"
    SCHEDULER_JOB_ID = "SCHEDULER_JOB_ID"


def app_config_from_env():
    secret_key = os.getenv(EnvConfig.SECRET.value, None)

    if not secret_key:
        _logger.warning(
            "Undefined secret $%s: Using default",
            EnvConfig.SECRET.value)

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

    scheduler_job_id = os.getenv(
        EnvConfig.SCHEDULER_JOB_ID.value,
        DEFAULT_ENV_CONFIG[EnvConfig.SCHEDULER_JOB_ID])

    return {
        AppConfig.SECRET_KEY.value: secret_key,
        AppConfig.REDIS_URL.value: redis_url,
        AppConfig.SPARQL_ENDPOINT.value: sparql,
        AppConfig.SPARQL_UPDATE_ENDPOINT.value: sparql_udpate,
        AppConfig.GRAPH_URI.value: graph_uri,
        AppConfig.SPARQL_USER.value: sparql_user,
        AppConfig.SPARQL_PASS.value: sparql_pass,
        AppConfig.VALIDATOR_DISABLED.value: validator_disabled,
        AppConfig.RESULT_TTL.value: result_ttl,
        AppConfig.SCHEDULER_JOB_ID.value: scheduler_job_id
    }
