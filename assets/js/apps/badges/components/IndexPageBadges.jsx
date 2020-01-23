import React, { Fragment } from 'react';
import ReactDOM from 'react-dom';

import ExperimentLastUpdatedBadge from './ExperimentLastUpdateBadge';
import PublicAccessBadge from './PublicAccessBadge';
import DatasetCountBadge from './DatasetCountBadge';
import DatafileCountBadge from './DatafileCountBadge';


document.querySelectorAll('.badges')
  .forEach((domContainer) => {
    const experimentID = domContainer.id.split('-')[1];
    ReactDOM.render(
      <Fragment>
        <ul className="list-inline float-right list-unstyled">
          <li className="mr-1 list-inline-item">
            <ExperimentLastUpdatedBadge experimentID={experimentID} />
          </li>
          <li className="mr-1 list-inline-item">
            <DatasetCountBadge experimentID={experimentID} />
          </li>
          <li className="mr-1 list-inline-item">
            <DatafileCountBadge experimentID={experimentID} />
          </li>
          <li className="mr-1 list-inline-item">
            <PublicAccessBadge experimentID={experimentID} />
          </li>
        </ul>
      </Fragment>, domContainer,
    );
  });
