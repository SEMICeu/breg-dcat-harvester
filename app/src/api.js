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
