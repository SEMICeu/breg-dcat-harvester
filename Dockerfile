FROM python:3.8-buster

ENV PATH_HARVESTER /harvester
ENV HARVESTER_PORT 5000
ENV HARVESTER_SERVER_SPAWN 5

RUN curl -sL https://deb.nodesource.com/setup_12.x | bash -
RUN apt-get update -y && apt-get install -y nodejs

RUN mkdir -p ${PATH_HARVESTER}
COPY . ${PATH_HARVESTER}
WORKDIR ${PATH_HARVESTER}
RUN ./build-app.sh
WORKDIR ${PATH_HARVESTER}/api
RUN pip install .

EXPOSE ${HARVESTER_PORT}

CMD ["/usr/local/bin/harvester"]