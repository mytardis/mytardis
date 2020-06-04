import React from "react";
import "./Project.css";
import Experiment from "../Experiment/Experiment";

const experimentList = (projectId) => {
  let experiments = [];
  for (let i = 0; i < 20; i++) {
    experiments.push({
      id: i,
      name: "project__" + projectId + "_experiment__" + i,
      description: "This is the description for experiment #" + i,
    });
  }
  return experiments;
};

async function getExperimentList(projectId) {
  let response = await fetch(
    `http://130.216.218.45:80/api/v1/experiment/?project__id=${projectId}`
  );
  let data = await response.json();
  // data probably isn't a list, need to access the field containing the list.
  return data.objects;
}

// async function fetchProject(projectId) {
// let response = await fetch(
//   `yapi/v1/project/?id=${projectId}`
// );
// let data = await response.json();
// console.log(data);
// return data;
// }

const fetchProject = (projectId) => {
  fetch(`http://localhost:8000/api/v1/project/?id=${projectId}`, {
    method: 'get',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    }
  }).then(response => {
    if (!response.ok) {
      throw new Error("An error on the server occurred.")
    }
    console.log(response)
    return response.json()
  })
}

const mockProjectData = () => {
  let mockProject = {
    meta: {
      limit: "int",
      next: "",
      offset: "int",
      previous: "",
      total_count: "int",
    },
    objects: {
      project: [
        {
          resource_uri: "",
          created_by: "related",
          parameter_sets: "related",
          institution: "related",
          id: 0,
          name: "MASS Spec Analysis 01",
          raid: "",
          description: "Data from mass spectrometry imaging by Nick Demarais.",
          locked: false,
          public_access: 0,
          embargo_until: "datetime",
          start_date: "datetime",
          end_date: "datetime",
          url: "",
        },
      ],
    },
  };
  console.log(mockProject);
  return mockProject;
};

const Project = ({ projectId }) => {
  let projectData = mockProjectData().objects.project[0];

  console.log("Fetching project data.");
  projectData = fetchProject(projectId);
  console.log(projectData);

  return (
    <div className="project">
      <h2 className="project__label">Project</h2>
      <h1 className="project__name">{projectData.name}</h1>
      <div className="project__description">{projectData.description}</div>
      <h3 className="table__header">Experiments in this project</h3>
      <table className="experiment__table">
        {experimentList(projectId).map((experiment) => {
          return <Experiment experiment={experiment} />;
        })}
      </table>
    </div>
  );
};

export default Project;
