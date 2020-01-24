import React, { Fragment } from 'react';
import ReactDOM from 'react-dom';

import ExperimentLastUpdatedBadge from './ExperimentLastUpdateBadge';
import PublicAccessBadge from './PublicAccessBadge';
import DatasetCountBadge from './DatasetCountBadge';
import DatafileCountBadge from './DatafileCountBadge';


const elem = document.querySelector('.badges');
const experimentID = elem.id.split('-')[1];
ReactDOM.render(
  <Fragment>
    <span className="mr-2">
      <DatasetCountBadge experimentID={experimentID} />
    </span>
    <span className="mr-2">
      <DatafileCountBadge experimentID={experimentID} />
    </span>
    <span className="mr-2">
      <ExperimentLastUpdatedBadge experimentID={experimentID} />
    </span>
    <span className="mr-2">
      <PublicAccessBadge experimentID={experimentID} />
    </span>
  </Fragment>, elem,
);
