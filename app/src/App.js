import "bootstrap/dist/css/bootstrap.css";
import React from "react";
import Container from "react-bootstrap/Container";
import Nav from "react-bootstrap/Nav";
import Navbar from "react-bootstrap/Navbar";
import { BrowserRouter, Link, Route } from "react-router-dom";
import { Slide, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import "./App.css";
import { ErrorBoundary } from "./ErrorBoundary";
import { SchedulerSection } from "./SchedulerSection";

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <ToastContainer transition={Slide} />
        <Navbar bg="dark" variant="dark" expand="lg">
          <Link to="/" className="navbar-brand">
            BReg DCAT Harvester
          </Link>
          <Navbar.Toggle aria-controls="basic-navbar-nav" />
          <Navbar.Collapse id="basic-navbar-nav">
            <Nav className="mr-auto">
              <Link to="/" className="nav-link">
                Scheduler
              </Link>
            </Nav>
          </Navbar.Collapse>
        </Navbar>
        <Container className="mt-4 mb-4">
          <Route exact path="/" component={SchedulerSection} />
        </Container>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
