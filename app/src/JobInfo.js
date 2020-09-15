import _ from "lodash";
import moment from "moment";
import React from "react";
import Badge from "react-bootstrap/Badge";
import Card from "react-bootstrap/Card";

function getBadgeVariant(status) {
  const variantMap = {
    finished: "success",
    failed: "warning",
  };

  return variantMap[_.toLower(status)] || "info";
}

export const JobInfo = ({ job }) => {
  const numTriples = _.get(job, "result.num_triples", undefined);

  return (
    <Card>
      <Card.Body>
        <Card.Subtitle className="mt-0 mb-1">
          <span className="mr-2">
            <Badge variant={getBadgeVariant(job.status)}>
              {_.capitalize(job.status)}
            </Badge>
          </span>
          <span>{`${moment(job.enqueued_at).format("ll")} ${moment(
            job.enqueued_at
          ).format("LTS")}`}</span>
        </Card.Subtitle>
        <Card.Text>
          <p className={numTriples === undefined ? "mb-0" : ""}>
            <code>{job.job_id}</code>
          </p>
          {numTriples !== undefined && (
            <p className="mb-0">
              Number of harvested triples:{" "}
              <strong className="text-info">{numTriples}</strong>
            </p>
          )}
        </Card.Text>
      </Card.Body>
    </Card>
  );
};
