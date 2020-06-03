import React from "react";
import "./Experiment.css";

const experiment = ({ experiment }) => {
  const experimentLink = `http://130.216.218/45/api/v1/experiment/${experiment.id}`;
  return (
    <tr>
      <td>
        <a className="experiment__link" href={experimentLink}>
          {experiment.name}
        </a>
      </td>
    </tr>
  );
};

export default experiment;
