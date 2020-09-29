import _ from "lodash";
import moment from "moment";
import React, { useEffect, useMemo, useState } from "react";
import Card from "react-bootstrap/Card";
import Col from "react-bootstrap/Col";
import Form from "react-bootstrap/Form";
import InputGroup from "react-bootstrap/InputGroup";
import Row from "react-bootstrap/Row";
import { fetchScheduledJob, updateScheduledJob } from "./api";
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

export const Scheduler = () => {
  const [job, setJob] = useState(undefined);
  const [loading, setLoading] = useState(false);

  const throwErr = useAsyncError();

  const getJob = useMemo(() => {
    return () => {
      setLoading(true);

      fetchScheduledJob()
        .then(setJob)
        .catch((err) => {
          throwErr(err);
        })
        .then(() => {
          setLoading(false);
        });
    };
  }, [throwErr]);

  const postJob = useMemo(() => {
    return (seconds) => {
      setLoading(true);

      updateScheduledJob({ seconds })
        .then(setJob)
        .catch((err) => {
          throwErr(err);
        })
        .then(() => {
          setLoading(false);
        });
    };
  }, [throwErr]);

  const onIntervalChange = useMemo(() => {
    return (ev) => {
      postJob(_.toInteger(ev.target.value));
    };
  }, [postJob]);

  useEffect(getJob, []);

  return (
    <>
      <LoadingSpinner show={loading} />
      {!!job && (
        <Card>
          <Card.Body>
            <Row className="align-items-center">
              <Col md>
                <InputGroup size="sm">
                  <InputGroup.Prepend>
                    <InputGroup.Text>Harvest interval</InputGroup.Text>
                  </InputGroup.Prepend>
                  <Form.Control
                    value={job.interval_seconds}
                    as="select"
                    onChange={onIntervalChange}
                  >
                    {_.chain(INTERVAL_OPTIONS)
                      .concat(job.interval_seconds)
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
              <Col md className="mt-md-0 mt-3">
                <span className="text-muted">Next job</span>
                <span className="ml-2">
                  {moment(job.next_date).local().format("lll")}
                </span>
              </Col>
            </Row>
          </Card.Body>
        </Card>
      )}
    </>
  );
};
