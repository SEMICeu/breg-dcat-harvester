import "bootstrap/dist/css/bootstrap.css";
import React, { useEffect, useState } from "react";
import Container from "react-bootstrap/Container";
import Navbar from "react-bootstrap/Navbar";
import { fetchJobs, fetchSources } from "./api";
import "./App.css";
import { ErrorBoundary } from "./ErrorBoundary";
import { LoadingSpinner } from "./LoadingSpinner";

function App() {
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);

    const promJobs = fetchJobs();
    const promSources = fetchSources();

    Promise.all([promJobs, promSources])
      .then((jobs, sources) => {
        console.log("jobs", jobs);
        console.log("sources", sources);
      })
      .then(() => {
        setLoading(false);
      });
  }, []);

  return (
    <>
      <LoadingSpinner show={loading} />
      <Navbar bg="dark" variant="dark" expand="lg">
        <Navbar.Brand>Base Registries Harvester</Navbar.Brand>
      </Navbar>
      <Container className="mt-4 mb-4">
        <ErrorBoundary>
          <h4>Hello World</h4>
        </ErrorBoundary>
      </Container>
    </>
  );
}

export default App;
