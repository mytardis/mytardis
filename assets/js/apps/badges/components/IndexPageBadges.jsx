import React, { Fragment } from 'react';
import ReactDOM from 'react-dom';

import ExperimentLastUpdatedBadge from './ExperimentLastUpdateBadge';
import PublicAccessBadge from './PublicAccessBadge';
import DatasetCountBadge from './DatasetCountBadge';
import DatafileCountBadge from "./DatafileCountBadge";


document.querySelectorAll('.badges')
  .forEach((domContainer) => {
    const experimentID = domContainer.id.split('-')[1];
    ReactDOM.render(
      <Fragment>
        <ExperimentLastUpdatedBadge experimentID={experimentID} />
        <DatasetCountBadge experimentID={experimentID} />
        <DatafileCountBadge experimentID={experimentID}/>
        <PublicAccessBadge experimentID={experimentID} />
      </Fragment>, domContainer,
    );
  });
