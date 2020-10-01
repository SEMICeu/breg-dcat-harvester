import "bootstrap/dist/css/bootstrap.css";
import _ from "lodash";
import React, { useMemo } from "react";
import Alert from "react-bootstrap/Alert";
import Col from "react-bootstrap/Col";
import Container from "react-bootstrap/Container";
import Navbar from "react-bootstrap/Navbar";
import Row from "react-bootstrap/Row";
import { useQuery } from "react-query";
import { Slide, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { fetchJobs, fetchSources } from "./api";
import "./App.css";
import { ErrorBoundary } from "./ErrorBoundary";
import { JobInfo } from "./JobInfo";
import { LoadingSpinner } from "./LoadingSpinner";
import { Scheduler } from "./Scheduler";
import { SourceInfo } from "./SourceInfo";

const REFETCH_INTERVAL_MS =
  _.toInteger(process.env.REACT_APP_REFETCH_INTERVAL_MS) || 20000;

const NUM_JOBS = _.toInteger(process.env.REACT_APP_NUM_JOBS) || 5;

function App() {
  const fetchJobsPartial = useMemo(() => {
    return () =>
      fetchJobs({ num: NUM_JOBS, extended: true }).then((jobs) => jobs || []);
  }, []);

  const queryJobs = useQuery("jobs", fetchJobsPartial, {
    refetchInterval: REFETCH_INTERVAL_MS,
  });

  const querySources = useQuery("sources", fetchSources, {
    refetchInterval: REFETCH_INTERVAL_MS,
  });

  const queryLoading = queryJobs.isLoading || querySources.isLoading;
  const queryError = queryJobs.isError || querySources.isError;

  return (
    <ErrorBoundary>
      <ToastContainer transition={Slide} />
      <LoadingSpinner show={queryLoading} />
      <Navbar bg="dark" variant="dark" expand="lg">
        <Navbar.Brand>BReg DCAT Harvester</Navbar.Brand>
      </Navbar>
      <Container className="mt-4 mb-4">
        {queryError ? (
          <Alert variant="danger">
            <Alert.Heading>An error occurred</Alert.Heading>
            <p className="mb-0">Please try again later</p>
          </Alert>
        ) : (
          <>
            <Row className="mb-3">
              <Col>
                <h4 className="mb-3">Scheduler</h4>
                <Scheduler runDisabled={_.isEmpty(querySources.data)} />
              </Col>
            </Row>
            {!!queryJobs.data && (
              <Row>
                <Col>
                  <h4>Recent harvest jobs</h4>
                  <p className="text-muted">
                    This list shows the latest <strong>{NUM_JOBS}</strong> jobs{" "}
                    <em>for each job status</em>
                  </p>
                  {_.isEmpty(queryJobs.data) ? (
                    <Alert variant="info">
                      No jobs were found in the server queue
                    </Alert>
                  ) : (
                    <Row>
                      {_.map(queryJobs.data, (job) => (
                        <Col key={job.job_id} lg={6} className="mb-3">
                          <JobInfo job={job} />
                        </Col>
                      ))}
                    </Row>
                  )}
                </Col>
              </Row>
            )}
            {!!querySources.data && (
              <Row>
                <Col>
                  <h4 className="mb-3">Configured sources</h4>
                  {_.isEmpty(querySources.data) ? (
                    <Alert variant="info">
                      There are no RDF sources configured
                    </Alert>
                  ) : (
                    <Row>
                      {_.map(querySources.data, (source) => (
                        <Col key={source.uri} className="mb-3">
                          <SourceInfo source={source} />
                        </Col>
                      ))}
                    </Row>
                  )}
                </Col>
              </Row>
            )}
          </>
        )}
      </Container>
    </ErrorBoundary>
  );
}

export default App;
