import React from 'react';
import ReactDOM from 'react-dom';

import ExperimentLastUpdatedBadge from "./ExperimentLastUpdateBadge";


document.querySelectorAll('.badges')
  .forEach(domContainer => {
    const experimentID = domContainer.id.split("-")[1];
    ReactDOM.render(
      <ExperimentLastUpdatedBadge experimentID={experimentID}/>, domContainer);
  });