import React, { Component, useState, useEffect } from "react";
import "./ProjectPage.css";
import ExperimentList from "../ExperimentList/ExperimentList";
import { Alert, Spinner } from "react-bootstrap";

export default function ProjectPage(props) {

  let [projectData, setProjectData] = useState(null);
  let [responseStatus, setResponseStatus] = useState(false);

  // fetches project data, sets state
  useEffect(() => {
    console.log("From use effect.");
    fetch(`/api/v1/project/?id=${props.projectId}`, {
      method: 'get',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      }
    }).then(response => {
      console.log(response)
      setResponseStatus(response.status)
      if (!response.ok) {
        throw new Error("An error on the server occurred.")
      }
      console.log('response was ok');
      response.json().then(projectData => {
        setProjectData(projectData)
      })
    })
  }, [])


  // render logic
  console.log("the project data: " + projectData);
  console.log(responseStatus);
  if (projectData == null) {
    return (
      <div>
        <Spinner animation="border" role="status" />
        <span className="sr-only">Loading...</span>
      </div>
    )
  }

  if (projectData.objects.length == 0) {
    return (
      <Alert variant="primary">
        No project was found containing the id <b>{props.projectId}</b>.<br/>
        Possible causes:
        <ul>
          <li>The project does not exist.</li>
          <li>You are not logged into MyTardis.</li>
          <li>You do not have access to view this project.</li>
        </ul>
      </Alert>
    )
  }

  let projectName = projectData.objects[0].name;
  let projectDescription = projectData.objects[0].description;
  return (
    <div className="project">
      <h2 className="project__label">Project</h2>
      <h1 className="project__name">{projectName}</h1>
      <div className="project__description">{projectDescription}</div>
      <ExperimentList projectId={props.projectId} />
    </div>
  );
}
