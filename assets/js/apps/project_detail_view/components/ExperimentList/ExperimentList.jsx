import React, { useState, useEffect } from "react";
import "./ExperimentList.css";

export default function ExperimentList(props) {
  let [experimentsData, setExperimentsData] = useState(null);
  let [resultLimit, setResultLimit] = useState(2000);

  // fetching experiment data by project id
  useEffect(() => {
    fetch(`/api/v1/experiment/?limit=${resultLimit}&project__id=${props.projectId}`, {
      method: 'get',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      }
    }).then(response => {
      console.log('experiment by project fetch response.')
      if (!response.ok) {
        throw new Error("An error occurred fetching experiments.")
      }
      console.log("experiment fetch response was OK.")
      response.json().then(experimentsData => {
        setExperimentsData(experimentsData)
      })
    })
  }, [])

  if (experimentsData == null) {
    return (
      <h1>Loading...</h1>
    )
  }

  const experiments = experimentsData.objects;
  return (
    <table className="experiment__table">
      <tbody>
        {experiments.map((experiment, index) => {
          console.log(experiment)
          let experimentLink = `/experiment/view/${experiment.id}`;
          return (
            <tr key={index}>
              <td>
                <a className="experiment__link" href={experimentLink}>
                  {experiment.title}
                </a>
              </td>
            </tr>
          )
        })}
      </tbody>
    </table>
  );
};