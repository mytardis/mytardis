import React, { Component, useState, useEffect } from "react";
import "./ProjectPage.css";
import Experiment from "../Experiment/Experiment";

class Project extends Component {
  constructor(props) {
    super(props);

    console.log("constr");

    this.state = {
      projectData: null,
    }
  }

  experimentList = (projectId) => {
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

  // getExperimentList(projectId) {
  //   let response = await fetch(
  //     `http://130.216.218.45:80/api/v1/experiment/?project__id=${projectId}`
  //   );
  //   let data = await response.json();
  //   // data probably isn't a list, need to access the field containing the list.
  //   return data.objects;
  // }

  componentWillMount() {
    console.log("from did mount");
    fetch(`http://localhost:8000/api/v1/project/?id=${this.props.projectId}`, {
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
        console.log(projectData);
        this.setState({
          projectData
        });
        // return response.json()
      })
    })
  }

  render() {
    // const { projectData } = this.state;
    // console.log("props " + this.props.projectId);
    console.log("the project data: " + this.state.projectData);
    let projectData = this.state.projectData;
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
        {/* <table className="experiment__table">
          {experimentList(projectId).map((experiment) => {
            return <Experiment experiment={experiment} />;
          })}
        </table> */}
      </div>
    );
  };
}

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
      {/* <table className="experiment__table">
          {experimentList(projectId).map((experiment) => {
            return <Experiment experiment={experiment} />;
          })}
        </table> */}
    </div>
  );
}

// export default Project;
