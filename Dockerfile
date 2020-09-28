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

CMD ["/usr/local/bin/gunicorn", "-b", "0.0.0.0:5000", "-w", "4", "-k", "eventlet", "--access-logfile", "-", "breg_harvester.app:create_app()"]