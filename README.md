# BREG-DCAT Harvester

Harvester tool for RDF datasets based on the [BRegDCAT](https://joinup.ec.europa.eu/collection/access-base-registries/solution/abr-specification-registry-registries) specification.

- The `api` folder contains a Flask-based HTTP API to manage asynchronous harvest jobs.
- The `app` folder contains a React-based application to serve as the user entrypoint to the API.

![Harvester diagram](diagram.png "Harvester diagram")

## API

### Configuration

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
| `HARVESTER_VALIDATOR_DISABLED`     | _None_                                    | Flag to disable the SHACL validator API.            |
| `HARVESTER_RESULT_TTL`             | `604800` _(7 days)_                       | Seconds that successful jobs will be kept in Redis. |

#### Data sources

Data sources are configured using the `$HARVESTER_SOURCES` environment variable. It should contain a list of lists in a JSON-serialized string. Each list item must contain two items:

- The URI of the data source.
- The format of the data source as [defined by rdflib](https://rdflib.readthedocs.io/en/stable/plugin_parsers.html).

For example:

```
export HARVESTER_SOURCES='[["https://gist.githubusercontent.com/agmangas/b07a69fd8a4d415c8e3d7a7dff7e41e5/raw/e3d574fdcdd14a11acce566c98486bca3a0f1fa4/breg-sample-01.xml", "xml"], ["https://gist.githubusercontent.com/agmangas/5f737b17ebf97c318e2ca3b4099c4c19/raw/5a1411286eb86a9689230ffcd3052a72fee05d74/breg-sample-02.ttl", "n3"]]'
```

This variable is then explicitly injected by the Compose file into the _api_ container.

### API Usage

Create a new harvest job:

```
$ curl -X POST http://localhost:9090/api/harvest/
{
	"description": "breg_harvester.harvest.run_harvest(graph_uri='http://fundacionctic.org/breg-harvester', sources=[<SourceDataset> Type='DataTypes.XML' URI='https://gist.githubusercontent.c..., store_kwargs={'query_endpoint': 'http://virtuoso:8890/sparql', 'update_endpoint': 'http:..., validator=<breg_harvester.harvest.DummyValidator object at 0x7f64feeb0790>)",
	"ended_at": null,
	"enqueued_at": "2020-09-14T09:13:33.429642",
	"exc_info": null,
	"job_id": "6d65ac39-1a84-4bba-8c0e-8c81d79b5cea",
	"result": null,
	"started_at": null,
	"status": "queued"
}
```

Fetch the current status of a previously created harvest job using the job ID provided in the _POST_ response:

```
$ curl -X GET http://localhost:9090/api/harvest/6d65ac39-1a84-4bba-8c0e-8c81d79b5cea
{
	"description": "breg_harvester.harvest.run_harvest(graph_uri='http://fundacionctic.org/breg-harvester', sources=[<SourceDataset> Type='DataTypes.XML' URI='https://gist.githubusercontent.c..., store_kwargs={'query_endpoint': 'http://virtuoso:8890/sparql', 'update_endpoint': 'http:..., validator=<breg_harvester.harvest.DummyValidator object at 0x7f64feeb0790>)",
	"ended_at": "2020-09-14T09:13:34.118779",
	"enqueued_at": "2020-09-14T09:13:33.429642",
	"exc_info": null,
	"job_id": "6d65ac39-1a84-4bba-8c0e-8c81d79b5cea",
	"result": {
		"num_triples": 22,
		"sources": [{
			"data_type": "xml",
			"format": "xml",
			"mime": "application/rdf+xml",
			"uri": "https://gist.githubusercontent.com/agmangas/b07a69fd8a4d415c8e3d7a7dff7e41e5/raw/e3d574fdcdd14a11acce566c98486bca3a0f1fa4/breg-sample-01.xml"
		}, {
			"data_type": "n3",
			"format": "n3",
			"mime": "text/turtle",
			"uri": "https://gist.githubusercontent.com/agmangas/5f737b17ebf97c318e2ca3b4099c4c19/raw/5a1411286eb86a9689230ffcd3052a72fee05d74/breg-sample-02.ttl"
		}]
	},
	"started_at": "2020-09-14T09:13:33.713726",
	"status": "finished"
}
```

Fetch the list of the most recently enqueued jobs:

```
$ curl -X GET http://localhost:9090/api/harvest/
{
	"failed": [],
	"finished": [{
		"ended_at": "2020-09-14T09:13:05.552509",
		"enqueued_at": "2020-09-14T09:13:04.384213",
		"job_id": "e3703999-2757-473a-ba72-87264e616891",
		"started_at": "2020-09-14T09:13:04.677173",
		"status": "finished"
	}, {
		"ended_at": "2020-09-14T09:13:32.703328",
		"enqueued_at": "2020-09-14T09:13:32.057127",
		"job_id": "695ef6d9-da83-4d5a-8403-e6cbc5095b3e",
		"started_at": "2020-09-14T09:13:32.296547",
		"status": "finished"
	}, {
		"ended_at": "2020-09-14T09:13:33.462166",
		"enqueued_at": "2020-09-14T09:13:32.793979",
		"job_id": "87d015b2-1f7e-40d6-a11f-0729296483b7",
		"started_at": "2020-09-14T09:13:33.050950",
		"status": "finished"
	}, {
		"ended_at": "2020-09-14T09:13:34.118779",
		"enqueued_at": "2020-09-14T09:13:33.429642",
		"job_id": "6d65ac39-1a84-4bba-8c0e-8c81d79b5cea",
		"started_at": "2020-09-14T09:13:33.713726",
		"status": "finished"
	}]
}
```
