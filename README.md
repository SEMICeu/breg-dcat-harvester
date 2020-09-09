# BREG-DCAT Harvester

## Configuration

| Variable                           | Default                                   | Description                                         |
| ---------------------------------- | ----------------------------------------- | --------------------------------------------------- |
| `HARVESTER_LOG_LEVEL`              | `debug`                                   | Log level of the API logger.                        |
| `HARVESTER_REDIS`                  | `redis://redis`                           | Redis URL for the jobs queue.                       |
| `HARVESTER_SPARQL_ENDPOINT`        | `http://virtuoso:8890/sparql`             | Virtuoso SPARQL query endpoint.                     |
| `HARVESTER_SPARQL_UPDATE_ENDPOINT` | `http://virtuoso:8890/sparql-auth`        | Virtuoso SPARQL update endpoint.                    |
| `HARVESTER_GRAPH_URI`              | `http://fundacionctic.org/breg-harvester` | Default graph URI.                                  |
| `HARVESTER_SPARQL_USER`            | `dba`                                     | User of the Virtuoso triple store.                  |
| `HARVESTER_SPARQL_PASS`            | `dba`                                     | Password for the user of the Virtuoso triple store. |
| `HARVESTER_PORT`                   | `5000`                                    | Port for the HTTP API server.                       |

### Data sources

Data sources are configured using the `$HARVESTER_SOURCES` environment variable. It should contain a list of lists in a JSON-serialized string. Each list item must contain two items:

- The URI of the data source.
- The format of the data source as [defined by rdflib](https://rdflib.readthedocs.io/en/stable/plugin_parsers.html).

For example:

```
export HARVESTER_SOURCES='[["https://gist.githubusercontent.com/agmangas/b07a69fd8a4d415c8e3d7a7dff7e41e5/raw/e3d574fdcdd14a11acce566c98486bca3a0f1fa4/breg-sample-01.xml", "xml"], ["https://gist.githubusercontent.com/agmangas/5f737b17ebf97c318e2ca3b4099c4c19/raw/5a1411286eb86a9689230ffcd3052a72fee05d74/breg-sample-02.ttl", "n3"]]'
```

This variable is then explicitly injected by the Compose file into the _api_ container.

## Usage

Create a new harvest job:

```
$ curl -X POST http://localhost:9090/api/harvest/
{"description":"breg_harvester.harvest.run_harvest(graph_uri='http://localhost/harvester', sources=[<SourceDataset> Type='DataTypes.XML' URI='https://gist.githubusercontent.c..., store_kwargs={'query_endpoint': 'http://virtuoso:8890/sparql', 'update_endpoint': 'http:..., validator=<breg_harvester.harvest.DummyValidator object at 0x7f33ae51fc70>)","ended_at":null,"enqueued_at":"2020-09-09T16:23:18.795852","job_id":"f5c77724-e271-4d3b-9cf2-8c6180ab0129","result":null,"started_at":null,"status":"queued"}
```

Fetch the current status of a previously created harvest job using the job ID provided in the _POST_ response:

```
$ curl -X GET http://localhost:9090/api/harvest/f5c77724-e271-4d3b-9cf2-8c6180ab0129
{"description":"breg_harvester.harvest.run_harvest(graph_uri='http://localhost/harvester', sources=[<SourceDataset> Type='DataTypes.XML' URI='https://gist.githubusercontent.c..., store_kwargs={'query_endpoint': 'http://virtuoso:8890/sparql', 'update_endpoint': 'http:..., validator=<breg_harvester.harvest.DummyValidator object at 0x7f33ae51fc70>)","ended_at":"2020-09-09T16:23:19.443338","enqueued_at":"2020-09-09T16:23:18.795852","job_id":"f5c77724-e271-4d3b-9cf2-8c6180ab0129","result":{"num_triples":22,"sources":[{"data_type":"xml","format":"xml","mime":"application/rdf+xml","uri":"https://gist.githubusercontent.com/agmangas/b07a69fd8a4d415c8e3d7a7dff7e41e5/raw/e3d574fdcdd14a11acce566c98486bca3a0f1fa4/breg-sample-01.xml"},{"data_type":"n3","format":"n3","mime":"text/turtle","uri":"https://gist.githubusercontent.com/agmangas/5f737b17ebf97c318e2ca3b4099c4c19/raw/5a1411286eb86a9689230ffcd3052a72fee05d74/breg-sample-02.ttl"}]},"started_at":"2020-09-09T16:23:19.045519","status":"finished"}
```
