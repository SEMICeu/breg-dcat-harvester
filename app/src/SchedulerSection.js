import _ from "lodash";
import React, { useMemo } from "react";
import Alert from "react-bootstrap/Alert";
import Col from "react-bootstrap/Col";
import Row from "react-bootstrap/Row";
import { useQuery } from "react-query";
import "react-toastify/dist/ReactToastify.css";
import { fetchJobs, fetchSources } from "./api";
import "./App.css";
import { JobInfo } from "./JobInfo";
import { LoadingSpinner } from "./LoadingSpinner";
import { Scheduler } from "./Scheduler";
import { SourceInfo } from "./SourceInfo";

const DEFAULT_REFETCH_INTERVAL_MS = 20000;
const DEFAULT_NUM_JOBS = 5;

export const SchedulerSection = ({ refetchIntervalMs, numJobs } = {}) => {
  refetchIntervalMs =
    _.toInteger(refetchIntervalMs) ||
    _.toInteger(process.env.REACT_APP_REFETCH_INTERVAL_MS) ||
    DEFAULT_REFETCH_INTERVAL_MS;

  numJobs =
    _.toInteger(numJobs) ||
    _.toInteger(process.env.REACT_APP_NUM_JOBS) ||
    DEFAULT_NUM_JOBS;

  const fetchJobsPartial = useMemo(() => {
    return () =>
      fetchJobs({ num: numJobs, extended: true }).then((jobs) => jobs || []);
  }, [numJobs]);

  const queryJobs = useQuery("jobs", fetchJobsPartial, {
    refetchInterval: refetchIntervalMs,
  });

  const querySources = useQuery("sources", fetchSources, {
    refetchInterval: refetchIntervalMs,
  });

  const queryLoading = queryJobs.isLoading || querySources.isLoading;
  const queryError = queryJobs.isError || querySources.isError;

  return (
    <>
      <LoadingSpinner show={queryLoading} />
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
                  This list shows the latest <strong>{numJobs}</strong> jobs{" "}
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
    </>
  );
};
