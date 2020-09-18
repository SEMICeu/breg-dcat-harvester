import React from "react";
import Card from "react-bootstrap/Card";

export const SourceInfo = ({ source }) => {
  return (
    <Card>
      <Card.Body>
        <dl className="row mb-0">
          <dt className="col-sm-3 col-lg-2 text-muted">URI</dt>
          <dd className="col-sm-9 col-lg-10">
            <code>{source.uri}</code>
          </dd>
          <dt className="col-sm-3 col-lg-2 text-muted">MIME type</dt>
          <dd className="col-sm-9 col-lg-10">{source.mime}</dd>
        </dl>
      </Card.Body>
    </Card>
  );
};
