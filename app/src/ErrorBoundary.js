import _ from "lodash";
import React from "react";
import Alert from "react-bootstrap/Alert";

export class ErrorBoundary extends React.Component {
  state = {
    error: undefined,
  };

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, errorInfo) {
    console.warn(error, errorInfo);
  }

  render() {
    const { error } = this.state;
    const errDescr = _.get(error, "response.data.description");

    if (error) {
      return (
        <Alert variant="warning">
          <Alert.Heading>Ha ocurrido un error</Alert.Heading>
          <code>{errDescr ? errDescr : _.toString(error)}</code>
        </Alert>
      );
    }

    return this.props.children;
  }
}
