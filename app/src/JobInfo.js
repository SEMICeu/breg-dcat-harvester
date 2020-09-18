import _ from "lodash";
import moment from "moment";
import React, { useMemo, useState } from "react";
import Badge from "react-bootstrap/Badge";
import Button from "react-bootstrap/Button";
import Card from "react-bootstrap/Card";
import Modal from "react-bootstrap/Modal";

function getBadgeVariant(status) {
  const variantMap = {
    finished: "success",
    failed: "warning",
  };

  return variantMap[_.toLower(status)] || "info";
}

const JobModal = ({ job, show, onClose }) => {
  const numTriples = _.get(job, "result.num_triples", undefined);
  const excInfo = _.get(job, "exc_info", undefined);

  const handleClose = useMemo(() => {
    return () => {
      onClose();
    };
  }, [onClose]);

  return (
    <Modal show={show} onHide={handleClose}>
      <Modal.Header closeButton>
        <Modal.Title>Job details</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <dl className="row mb-0">
          {!!job.job_id && <dt className="col-lg-4 text-muted">Job ID</dt>}
          {!!job.job_id && (
            <dd className="col-lg-8">
              <code>{job.job_id}</code>
            </dd>
          )}
          {!!job.enqueued_at && (
            <dt className="col-lg-4 text-muted">Enqueued at</dt>
          )}
          {!!job.enqueued_at && (
            <dd className="col-lg-8">
              {moment.utc(job.enqueued_at).local().format("lll")}
            </dd>
          )}
          {!!job.started_at && (
            <dt className="col-lg-4 text-muted">Started at</dt>
          )}
          {!!job.started_at && (
            <dd className="col-lg-8">
              {moment.utc(job.started_at).local().format("lll")}
            </dd>
          )}
          {!!job.ended_at && <dt className="col-lg-4 text-muted">Ended at</dt>}
          {!!job.ended_at && (
            <dd className="col-lg-8">
              {moment.utc(job.ended_at).local().format("lll")}
            </dd>
          )}
          {!!job.status && <dt className="col-lg-4 text-muted">Status</dt>}
          {!!job.status && (
            <dd className="col-lg-8">{_.capitalize(job.status)}</dd>
          )}
        </dl>
        {!_.isNil(numTriples) && (
          <Card bg="success" text="white" className="mt-2">
            <Card.Body>
              <span className="mr-1">Resulting number of triples:</span>
              <strong>{numTriples}</strong>
            </Card.Body>
          </Card>
        )}
        {!_.isNil(excInfo) && (
          <Card bg="warning" className="mt-2">
            <Card.Body>
              <small>
                <pre className="mb-0">{excInfo}</pre>
              </small>
            </Card.Body>
          </Card>
        )}
      </Modal.Body>
    </Modal>
  );
};

export const JobInfo = ({ job }) => {
  const [show, setShow] = useState(false);
  const jobMoment = moment.utc(job.enqueued_at).local();

  const onShow = useMemo(() => {
    return () => {
      setShow(true);
    };
  }, []);

  const onClose = useMemo(() => {
    return () => {
      setShow(false);
    };
  }, []);

  return (
    <Card>
      <Card.Body>
        <Card.Subtitle className="mt-0 mb-1">
          <span className="mr-2">
            <Badge variant={getBadgeVariant(job.status)}>
              {_.capitalize(job.status)}
            </Badge>
          </span>
          <span>{`${jobMoment.format("ll")} ${jobMoment.format("LTS")}`}</span>
        </Card.Subtitle>
        <Card.Text>
          <code>{job.job_id}</code>
        </Card.Text>
        <Card.Text>
          <Button
            variant="light"
            size="sm"
            className="stretched-link"
            onClick={onShow}
          >
            View job details
          </Button>
        </Card.Text>
        <JobModal job={job} show={show} onClose={onClose} />
      </Card.Body>
    </Card>
  );
};
