import React from "react";
import Modal from "react-bootstrap/Modal";
import ModalBody from "react-bootstrap/ModalBody";
import Spinner from "react-bootstrap/Spinner";
import "./LoadingSpinner.css";

export const LoadingSpinner = ({ show }) => {
  return (
    <Modal
      show={show}
      className="loading-modal"
      autoFocus={false}
      backdrop="static"
    >
      <ModalBody className="text-center p-4">
        <Spinner animation="border" role="status" variant="light">
          <span className="sr-only">Loading...</span>
        </Spinner>
      </ModalBody>
    </Modal>
  );
};
