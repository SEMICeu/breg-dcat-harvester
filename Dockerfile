FROM python:3.8

ENV PATH_APP /app
ENV BREG_PORT 80
ENV BREG_SERVER_SPAWN 5
ENV BREG_LOG_LEVEL info

RUN mkdir -p ${PATH_APP}
COPY . ${PATH_APP}
WORKDIR ${PATH_APP}
RUN pip install .
EXPOSE 80

CMD ["/usr/local/bin/harvester"]