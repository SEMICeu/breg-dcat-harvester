import _ from "lodash";
import React, { useCallback, useEffect, useState } from "react";
import Button from "react-bootstrap/Button";
import Card from "react-bootstrap/Card";
import Col from "react-bootstrap/Col";
import Nav from "react-bootstrap/Nav";
import Row from "react-bootstrap/Row";
import Tab from "react-bootstrap/Tab";
import { fetchFacets } from "./api";
import { LoadingSpinner } from "./LoadingSpinner";
import { useAsyncError } from "./utils";

export const BrowserSection = () => {
  const [loading, setLoading] = useState(false);
  const [facets, setFacets] = useState(undefined);
  const [selectedFacets, setSelectedFacets] = useState({});

  const throwErr = useAsyncError();

  const isFacetSelected = useCallback(
    ({ facetKey, facetItem }) => {
      return _.some(
        selectedFacets[facetKey],
        (item) => item.n3 === facetItem.n3
      );
    },
    [selectedFacets]
  );

  const onFacetClick = useCallback(
    ({ facetKey, facetItem }) => {
      const arrSelected = selectedFacets[facetKey] || [];

      if (isFacetSelected({ facetKey, facetItem })) {
        _.remove(arrSelected, (item) => item.n3 === facetItem.n3);
      } else {
        arrSelected.push(facetItem);
      }

      selectedFacets[facetKey] = arrSelected;
      setSelectedFacets({ ...selectedFacets });
    },
    [isFacetSelected, selectedFacets]
  );

  useEffect(() => {
    setLoading(true);

    fetchFacets()
      .then(setFacets)
      .catch(throwErr)
      .then(() => {
        setLoading(false);
      });
  }, [throwErr]);

  return (
    <>
      <LoadingSpinner show={loading} />
      {!!facets && (
        <Row>
          <Col>
            <Row>
              <Col md>
                <h4>Search for datasets</h4>
                <p className="text-muted">
                  Use the filters below to find instances of{" "}
                  <code>dcat:Dataset</code>
                </p>
              </Col>
              <Col md="auto">
                <Button className="mb-3">Apply search filters</Button>
              </Col>
            </Row>
            <Card>
              <Card.Body className="pl-4">
                <Tab.Container
                  id="left-tabs-example"
                  defaultActiveKey={_.first(_.keys(facets))}
                >
                  <Row>
                    <Col md={4} className="mb-3 mb-md-0">
                      <small>
                        <Nav variant="pills" className="flex-column">
                          {_.map(_.keys(facets), (facetKey) => (
                            <Nav.Item key={facetKey}>
                              <Nav.Link eventKey={facetKey}>
                                {`${_.startCase(facetKey)} (${
                                  (selectedFacets[facetKey] || []).length
                                })`}
                              </Nav.Link>
                            </Nav.Item>
                          ))}
                        </Nav>
                      </small>
                    </Col>
                    <Col md={8}>
                      <Tab.Content>
                        {_.map(facets, (items, facetKey) => (
                          <Tab.Pane key={facetKey} eventKey={facetKey}>
                            {_.map(items, (facetItem, idx) => (
                              <Button
                                key={`${facetKey}-${idx}`}
                                variant={
                                  isFacetSelected({ facetKey, facetItem })
                                    ? "info"
                                    : "light"
                                }
                                size="sm"
                                className="mr-2 mb-2 text-left"
                                onClick={() => {
                                  onFacetClick({ facetKey, facetItem });
                                }}
                              >
                                {facetItem.label ? (
                                  facetItem.label
                                ) : (
                                  <code
                                    className={
                                      isFacetSelected({ facetKey, facetItem })
                                        ? "text-light"
                                        : "text-dark"
                                    }
                                  >
                                    {facetItem.n3}
                                  </code>
                                )}
                              </Button>
                            ))}
                          </Tab.Pane>
                        ))}
                      </Tab.Content>
                    </Col>
                  </Row>
                </Tab.Container>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}
    </>
  );
};
