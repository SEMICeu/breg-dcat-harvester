import React from "react";
import Badge from "react-bootstrap/Badge";
import Card from "react-bootstrap/Card";

export const SourceInfo = ({ source }) => {
  return (
    <Card>
      <Card.Body>
        <Card.Title className="mt-0 mb-2">
          <Badge variant="light">{source.mime}</Badge>
        </Card.Title>
        <Card.Text>
          <small>
            <samp className="text-muted">{source.uri}</samp>
          </small>
        </Card.Text>
      </Card.Body>
    </Card>
  );
};
