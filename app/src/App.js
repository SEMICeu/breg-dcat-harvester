import "bootstrap/dist/css/bootstrap.css";
import _ from "lodash";
import React, { useEffect, useState } from "react";
import Alert from "react-bootstrap/Alert";
import Col from "react-bootstrap/Col";
import Container from "react-bootstrap/Container";
import Navbar from "react-bootstrap/Navbar";
import Row from "react-bootstrap/Row";
import { fetchJobs, fetchSources } from "./api";
import "./App.css";
import { ErrorBoundary } from "./ErrorBoundary";
import { JobInfo } from "./JobInfo";
import { LoadingSpinner } from "./LoadingSpinner";

function App() {
  const [loading, setLoading] = useState(false);
  const [jobs, setJobs] = useState(undefined);
  const [sources, setSources] = useState(undefined);
  const [error, setError] = useState(undefined);

  useEffect(() => {
    setLoading(true);

    Promise.all([fetchJobs(), fetchSources()])
      .then(([jobs, sources]) => {
        setJobs(jobs);
        setSources(sources);
      })
      .catch((err) => {
        setError(err);
      })
      .then(() => {
        setLoading(false);
      });
  }, []);

  return (
    <>
      <LoadingSpinner show={loading} />
      <Navbar bg="dark" variant="dark" expand="lg">
        <Navbar.Brand>BREG Harvester</Navbar.Brand>
      </Navbar>
      <Container className="mt-4 mb-4">
        <ErrorBoundary>
          {!!jobs && (
            <>
              <h4 className="mb-3">Recent harvest jobs</h4>
              {_.isEmpty(jobs) ? (
                <Alert variant="info">
                  No jobs were found in the server queue
                </Alert>
              ) : (
                <Row>
                  {_.map(jobs, (job) => (
                    <Col key={job.job_id} lg={6} className="mb-3">
                      <JobInfo job={job} />
                    </Col>
                  ))}
                </Row>
              )}
            </>
          )}
        </ErrorBoundary>
      </Container>
    </>
  );
}

export default App;
