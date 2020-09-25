import _ from "lodash";
import moment from "moment";
import React, { useEffect, useMemo, useState } from "react";
import Card from "react-bootstrap/Card";
import Col from "react-bootstrap/Col";
import Form from "react-bootstrap/Form";
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

  useEffect(getJob, []);

  return (
    <>
      <LoadingSpinner show={loading} />
      {!!job && (
        <Card>
          <Card.Body>
            <Row>
              <Col md>
                <dl className="row mb-0">
                  <dt className="col-lg-3 text-muted">Job ID</dt>
                  <dd className="col-lg-9">
                    <code>{job.id}</code>
                  </dd>
                  <dt className="col-lg-3 text-muted">Interval</dt>
                  <dd className="col-lg-9">
                    {moment
                      .duration(job.interval_seconds, "seconds")
                      .humanize()}
                  </dd>
                  <dt className="col-lg-3 text-muted">Next job</dt>
                  <dd className="col-lg-9">
                    {moment(job.next_date).local().format("lll")}
                  </dd>
                </dl>
              </Col>
              <Col md>
                <Form.Group className="mb-0">
                  <Form.Label className="text-muted">
                    Select to update interval
                  </Form.Label>
                  <Form.Control
                    value={job.interval_seconds}
                    as="select"
                    onChange={(ev) => {
                      postJob(_.toInteger(ev.target.value));
                    }}
                  >
                    {_.map(INTERVAL_OPTIONS, (val) => (
                      <option key={val} value={val}>
                        {moment.duration(val, "seconds").humanize()}
                      </option>
                    ))}
                  </Form.Control>
                </Form.Group>
              </Col>
            </Row>
          </Card.Body>
        </Card>
      )}
    </>
  );
};
