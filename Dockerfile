FROM python:3.6-buster

ENV PATH_HARVESTER /harvester

RUN curl -sL https://deb.nodesource.com/setup_12.x | bash -
RUN apt-get update -y && apt-get install -y nodejs

RUN mkdir -p ${PATH_HARVESTER}
COPY . ${PATH_HARVESTER}
WORKDIR ${PATH_HARVESTER}
RUN ./build-app.sh
WORKDIR ${PATH_HARVESTER}/api
RUN pip install .

EXPOSE 5000

# The --preload flag is necessary to avoid duplicating scheduler executions:
# https://stackoverflow.com/a/40162246

CMD ["/usr/local/bin/gunicorn", \
    "--bind", "0.0.0.0:5000", \
    "--workers", "4", \
    "--worker-class", "eventlet", \
    "--access-logfile", "-", \
    "--preload", \
    "breg_harvester.app:create_app()"]