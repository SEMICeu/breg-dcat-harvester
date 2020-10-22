import axios from "axios";
import _ from "lodash";
import moment from "moment";

export async function fetchJobs(
  { num, extended } = { num: 5, extended: true }
) {
  const response = await axios.get("/api/harvest/", {
    params: {
      num,
      extended,
    },
  });

  return _.chain(response.data)
    .values()
    .concat()
    .flatten()
    .sortBy((item) => moment(item.enqueued_at).unix())
    .reverse()
    .value();
}

export async function fetchSources() {
  const response = await axios.get("/api/harvest/source");
  return response.data;
}

export async function createJob() {
  const response = await axios.post("/api/harvest/");
  return response.data;
}

export async function fetchScheduledJob() {
  const response = await axios.get("/api/scheduler/");
  return response.data;
}

export async function updateScheduledJob({ seconds }) {
  const response = await axios.post("/api/scheduler/", {
    interval: seconds,
  });

  return response.data;
}

export async function fetchFacets() {
  const params = { ext: "true" };

  const responses = await Promise.all([
    axios.get("/api/browser/catalog/publisher/type", { params }),
    axios.get("/api/browser/dataset/theme", { params }),
    axios.get("/api/browser/catalog/language", { params }),
    axios.get("/api/browser/catalog/location", { params }),
    axios.get("/api/browser/catalog/taxonomy", { params }),
  ]);

  const facetKeys = [
    "publisherType",
    "theme",
    "language",
    "location",
    "themeTaxonomy",
  ];

  return _.chain(facetKeys)
    .map((key, idx) => [key, responses[idx].data])
    .fromPairs()
    .value();
}

export async function searchDatasets({ limit, filters } = { limit: 50 }) {
  const response = await axios.post("/api/browser/dataset/search", {
    limit,
    filters: filters || {},
  });

  return response.data;
}
