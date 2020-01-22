import React, { Fragment } from 'react';
import ReactDOM from 'react-dom';

import ExperimentLastUpdatedBadge from './ExperimentLastUpdateBadge';
import PublicAccessBadge from './PublicAccessBadge';


document.querySelectorAll('.badges')
  .forEach((domContainer) => {
    const experimentID = domContainer.id.split('-')[1];
    ReactDOM.render(
      <Fragment>
        <ExperimentLastUpdatedBadge experimentID={experimentID} />
        <PublicAccessBadge experimentID={experimentID} />
      </Fragment>, domContainer,
    );
  });
