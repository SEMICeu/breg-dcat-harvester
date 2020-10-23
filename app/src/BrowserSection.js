import _ from "lodash";
import React, { useCallback, useEffect, useState } from "react";
import Badge from "react-bootstrap/Badge";
import Button from "react-bootstrap/Button";
import Card from "react-bootstrap/Card";
import Col from "react-bootstrap/Col";
import Nav from "react-bootstrap/Nav";
import Row from "react-bootstrap/Row";
import Tab from "react-bootstrap/Tab";
import { FiCircle, FiDownloadCloud, FiSearch } from "react-icons/fi";
import { fetchFacets, searchDatasets } from "./api";
import { LoadingSpinner } from "./LoadingSpinner";
import { useAsyncError } from "./utils";

const REGEX_URL = /<(http.+)>/;
const REGEX_TYPE = /<https:\/\/www.w3.org\/ns\/iana\/media-types\/(.+)#Resource>/;

const CLASS_DT = "col-md-2 text-muted";
const CLASS_DD = "col-md-10";

const parseDistribution = ({ item }) => {
  const urlResult = REGEX_URL.exec(item.url);
  const typeResult = REGEX_TYPE.exec(item.type);

  if (!urlResult || !typeResult) {
    return;
  }

  const url = urlResult[1];
  const mediaType = typeResult[1];

  return { url, mediaType };
};

const DatasetPropDT = ({ name, type }) => {
  return (
    <dt className={CLASS_DT}>
      {name}
      <br />
      <code className="text-info">{type}</code>
    </dt>
  );
};

const DatasetPropDD = ({ dataset, dsetKey, isURI }) => {
  return (
    <dd className={CLASS_DD}>
      {_.map(_.get(dataset, dsetKey), (val, idx) => (
        <p
          className={idx === _.get(dataset, dsetKey).length - 1 ? "mb-0" : ""}
          key={`${dsetKey}-${idx}`}
        >
          {isURI ? <code>{val}</code> : val}
        </p>
      ))}
    </dd>
  );
};

const DatasetCard = ({ dataset }) => {
  return (
    <small>
      <Card>
        <Card.Header>{_.first(dataset.title)}</Card.Header>
        <Card.Body>
          {_.map(dataset.distribution, (item) => {
            const dist = parseDistribution({ item });

            return dist ? (
              <p key={dist.url}>
                <a href={dist.url}>
                  <FiDownloadCloud className="mr-2" />
                  {dist.mediaType}
                </a>
              </p>
            ) : null;
          })}
          <dl className="row mb-0">
            <DatasetPropDT name="Catalog" type="dcat:Catalog" />
            <dd className={CLASS_DD}>
              <code>{dataset.catalog}</code>
            </dd>
            <DatasetPropDT name="Identifier" type="rdfs:Literal" />
            <DatasetPropDD dataset={dataset} dsetKey="identifier" />
            <DatasetPropDT name="Description" type="rdfs:Literal" />
            <DatasetPropDD dataset={dataset} dsetKey="description" />
            <DatasetPropDT name="Language" type="dct:LinguisticSystem" />
            <DatasetPropDD dataset={dataset} dsetKey="language" isURI={true} />
            <DatasetPropDT name="Theme" type="skos:Concept" />
            <DatasetPropDD dataset={dataset} dsetKey="theme" isURI={true} />
            <DatasetPropDT name="Location" type="dct:Location" />
            <DatasetPropDD dataset={dataset} dsetKey="location" isURI={true} />
          </dl>
        </Card.Body>
      </Card>
    </small>
  );
};

const DatasetSearchSummary = ({ datasets, datasetFacets }) => {
  return (
    <div>
      <span className="mr-2">
        <small>
          Found <strong>{_.keys(datasets).length}</strong> datasets
        </small>
      </span>
      {_.map(datasetFacets, (facetsArr, facetKey) =>
        _.map(facetsArr, (facetItem) => (
          <Badge
            variant="light"
            key={`${facetKey}-${facetItem.n3}`}
            className="mr-2 text-left"
          >
            <span className="text-muted mr-2">{_.startCase(facetKey)}</span>
            {facetItem.label || <code class="text-wrap">{facetItem.n3}</code>}
          </Badge>
        ))
      )}
    </div>
  );
};

export const BrowserSection = () => {
  const [loading, setLoading] = useState(false);
  const [facets, setFacets] = useState(undefined);
  const [selectedFacets, setSelectedFacets] = useState({});
  const [datasets, setDatasets] = useState(undefined);
  const [datasetFacets, setDatasetFacets] = useState(undefined);

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
      const arrFacetKey = selectedFacets[facetKey] || [];

      if (isFacetSelected({ facetKey, facetItem })) {
        _.remove(arrFacetKey, (item) => item.n3 === facetItem.n3);
      } else {
        arrFacetKey.push(facetItem);
      }

      if (_.isEmpty(arrFacetKey)) {
        _.unset(selectedFacets, facetKey);
      } else {
        selectedFacets[facetKey] = arrFacetKey;
      }

      setSelectedFacets({ ...selectedFacets });
    },
    [isFacetSelected, selectedFacets]
  );

  const clearFilters = useCallback(() => {
    setSelectedFacets({});
  }, []);

  const getNumFilters = useCallback(() => {
    return _.chain(selectedFacets)
      .values()
      .map((arr) => (arr ? arr.length : 0))
      .sum()
      .value();
  }, [selectedFacets]);

  const onSearchClick = useCallback(() => {
    setLoading(true);

    const filters = _.chain(selectedFacets)
      .mapValues((arrItems) => _.map(arrItems, (item) => item.n3))
      .value();

    searchDatasets({ filters })
      .then((datasets) => {
        setDatasets(datasets);
        setDatasetFacets(_.cloneDeep(selectedFacets));
      })
      .catch(throwErr)
      .then(() => {
        setLoading(false);
      });
  }, [selectedFacets, throwErr]);

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
                <Button
                  variant="outline-secondary"
                  className="mb-3 mr-2"
                  onClick={clearFilters}
                  disabled={getNumFilters() === 0}
                >
                  <FiCircle className="mr-2" />
                  <span className="align-middle">
                    Clear <strong>{getNumFilters()}</strong> filters
                  </span>
                </Button>
                <Button
                  variant="primary"
                  className="mb-3"
                  onClick={onSearchClick}
                >
                  <FiSearch className="mr-2" />
                  <span className="align-middle">Search</span>
                </Button>
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
                                  (facets[facetKey] || []).length
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
      {!!datasets && !!datasetFacets && (
        <Row className="mt-3 text-muted">
          <Col>
            <DatasetSearchSummary
              datasets={datasets}
              datasetFacets={datasetFacets}
            />
          </Col>
        </Row>
      )}
      {!!datasets &&
        _.map(datasets, (dataset, datasetURI) => (
          <Row key={datasetURI} className="mt-3">
            <Col>
              <DatasetCard dataset={dataset} />
            </Col>
          </Row>
        ))}
    </>
  );
};
