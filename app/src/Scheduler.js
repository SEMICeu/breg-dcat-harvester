import _ from "lodash";
import moment from "moment";
import React, { useEffect, useMemo, useState } from "react";
import Button from "react-bootstrap/Button";
import Card from "react-bootstrap/Card";
import Col from "react-bootstrap/Col";
import Form from "react-bootstrap/Form";
import InputGroup from "react-bootstrap/InputGroup";
import Row from "react-bootstrap/Row";
import { toast } from "react-toastify";
import { createJob, fetchScheduledJob, updateScheduledJob } from "./api";
import { LoadingSpinner } from "./LoadingSpinner";
import { useAsyncError } from "./utils";

const INTERVAL_OPTIONS = [
  1800,
  3600,
  3600 * 2,
  3600 * 6,
  3600 * 24,
  3600 * 24 * 5,
  3600 * 24 * 15,
  3600 * 24 * 30,
];

export const Scheduler = ({ runDisabled } = {}) => {
  const [scheduledJob, setScheduledJob] = useState(undefined);
  const [loading, setLoading] = useState(false);

  const throwErr = useAsyncError();

  const runNow = useMemo(() => {
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
        .catch(throwErr)
        .then(() => {
          setLoading(false);
        });
    };
  }, [throwErr]);

  const getSchedule = useMemo(() => {
    return () => {
      setLoading(true);

      fetchScheduledJob()
        .then(setScheduledJob)
        .catch(throwErr)
        .then(() => {
          setLoading(false);
        });
    };
  }, [throwErr]);

  const updateSchedule = useMemo(() => {
    return (seconds) => {
      setLoading(true);

      updateScheduledJob({ seconds })
        .then(setScheduledJob)
        .catch(throwErr)
        .then(() => {
          setLoading(false);
        });
    };
  }, [throwErr]);

  const onIntervalChange = useMemo(() => {
    return (ev) => {
      updateSchedule(_.toInteger(ev.target.value));
    };
  }, [updateSchedule]);

  useEffect(getSchedule, []);

  return (
    <>
      <LoadingSpinner show={loading} />
      {!!scheduledJob && (
        <Card>
          <Card.Body>
            <Row className="align-items-center">
              <Col lg>
                <InputGroup size="sm">
                  <InputGroup.Prepend>
                    <InputGroup.Text>Harvest interval</InputGroup.Text>
                  </InputGroup.Prepend>
                  <Form.Control
                    value={scheduledJob.interval_seconds}
                    as="select"
                    onChange={onIntervalChange}
                  >
                    {_.chain(INTERVAL_OPTIONS)
                      .concat(scheduledJob.interval_seconds)
                      .sortBy()
                      .uniq()
                      .map((val) => (
                        <option key={val} value={val}>
                          {moment.duration(val, "seconds").humanize()}
                        </option>
                      ))
                      .value()}
                  </Form.Control>
                </InputGroup>
              </Col>
              <Col lg className="mt-lg-0 mt-3">
                <span className="text-muted">Next job</span>
                <span className="ml-2">
                  {moment(scheduledJob.next_date).local().format("lll")}
                </span>
              </Col>
              <Col lg="auto" className="mt-lg-0 mt-3">
                <Button
                  variant="primary"
                  size="sm"
                  disabled={!!runDisabled}
                  onClick={runNow}
                >
                  Run now
                </Button>
              </Col>
            </Row>
          </Card.Body>
        </Card>
      )}
    </>
  );
};
