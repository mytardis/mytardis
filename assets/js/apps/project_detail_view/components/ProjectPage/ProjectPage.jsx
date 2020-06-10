import React, { Component, useState, useEffect } from "react";
import "./ProjectPage.css";
import ExperimentList from "../ExperimentList/ExperimentList";

export default function ProjectPage(props) {

  let [projectData, setProjectData] = useState(null);

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
  if (projectData == null) {
    return (<h1>Loading...</h1>)
  }
  let projectName = projectData.objects[0].name;
  let projectDescription = projectData.objects[0].description;
  return (
    <div className="project">
      <h2 className="project__label">Project</h2>
      <h1 className="project__name">{projectName}</h1>
      <div className="project__description">{projectDescription}</div>
      <h3 className="table__header">Experiments in this project</h3>
        <ExperimentList projectId={props.projectId} />
    </div>
  );
}
