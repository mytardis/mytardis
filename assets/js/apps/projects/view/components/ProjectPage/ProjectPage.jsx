import React, { Component, useState, useEffect } from "react";
import "./ProjectPage.css";
import ExperimentList from "../ExperimentList/ExperimentList";
import { Alert, Spinner } from "react-bootstrap";

export default function ProjectPage(props) {

  return (
    <div className="project">
      <ExperimentList projectId={props.projectId} />
    </div>
  );
}
