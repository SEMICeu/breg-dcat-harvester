import "bootstrap/dist/css/bootstrap.css";
import _ from "lodash";
import React, { useMemo, useState } from "react";
import Alert from "react-bootstrap/Alert";
import Button from "react-bootstrap/Button";
import Col from "react-bootstrap/Col";
import Container from "react-bootstrap/Container";
import Navbar from "react-bootstrap/Navbar";
import Row from "react-bootstrap/Row";
import { useQuery } from "react-query";
import { Slide, toast, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { createJob, fetchJobs, fetchSources } from "./api";
import "./App.css";
import { ErrorBoundary } from "./ErrorBoundary";
import { JobInfo } from "./JobInfo";
import { LoadingSpinner } from "./LoadingSpinner";
import { Scheduler } from "./Scheduler";
import { SourceInfo } from "./SourceInfo";

const REFETCH_INTERVAL_MS =
  _.toInteger(process.env.REACT_APP_REFETCH_INTERVAL_MS) || 10000;

function App() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(undefined);

  const fetchJobsPartial = useMemo(() => {
    return () =>
      fetchJobs({ num: 5, extended: true }).then((jobs) => jobs || []);
  }, []);

  const queryJobs = useQuery("jobs", fetchJobsPartial, {
    refetchInterval: REFETCH_INTERVAL_MS,
  });

  const querySources = useQuery("sources", fetchSources, {
    refetchInterval: REFETCH_INTERVAL_MS,
  });

  const onNewJob = useMemo(() => {
    return () => {
      setLoading(true);

      createJob()
        .then((job) => {
          toast.success(
            <small>
              Harvest job added to queue:
              <br />
              <strong>{job.job_id}</strong>
            </small>,
            {
              position: "top-right",
              autoClose: 5000,
              hideProgressBar: true,
              closeOnClick: true,
              pauseOnHover: true,
              draggable: true,
              progress: undefined,
            }
          );
        })
        .catch(setError)
        .then(() => {
          setLoading(false);
        });
    };
  }, []);

  const queryLoading = queryJobs.isLoading || querySources.isLoading;
  const queryError = queryJobs.isError || querySources.isError;

  return (
    <ErrorBoundary>
      <ToastContainer transition={Slide} />
      <LoadingSpinner show={loading || queryLoading} />
      <Navbar bg="dark" variant="dark" expand="lg">
        <Navbar.Brand>BReg DCAT Harvester</Navbar.Brand>
      </Navbar>
      <Container className="mt-4 mb-4">
        {error || queryError ? (
          <Alert variant="danger">
            <Alert.Heading>An error occurred</Alert.Heading>
            <p className="mb-0">
              {error
                ? _.get(error, "response.data.description") || _.toString(error)
                : "Please try again later"}
            </p>
          </Alert>
        ) : (
          <>
            <Row className="mb-3">
              <Col>
                <h4 className="mb-3">Scheduler</h4>
                <Scheduler />
              </Col>
            </Row>
            {!!queryJobs.data && (
              <Row>
                <Col>
                  <h4 className="mb-3">Recent harvest jobs</h4>
                  <Button
                    variant="outline-primary"
                    className="mb-3"
                    onClick={onNewJob}
                    disabled={_.isEmpty(querySources.data)}
                  >
                    Enqueue new harvest job
                  </Button>
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
