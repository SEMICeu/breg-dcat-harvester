import axios from "axios";

export async function fetchJobs() {
  const response = await axios.get("/api/harvest/");
  return response.data;
}

export async function fetchSources() {
  const response = await axios.get("/api/harvest/source");
  return response.data;
}
