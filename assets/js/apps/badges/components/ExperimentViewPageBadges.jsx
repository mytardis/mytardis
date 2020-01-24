import React, { Fragment, useState } from 'react';
import ReactDOM from 'react-dom';

import PropTypes from 'prop-types';
import ExperimentLastUpdatedBadge from './ExperimentLastUpdateBadge';
import PublicAccessBadge from './PublicAccessBadge';
import DatasetCountBadge from './DatasetCountBadge';
import DatafileCountBadge from './DatafileCountBadge';
import fetchExperimentData from './utils/FetchData';


const ExperimentViewPageBadges = ({ experimentID }) => {
  const [expData, setExpData] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  React.useEffect(() => {
    fetchExperimentData(experimentID).then((data) => {
      setExpData(data);
      setIsLoading(false);
    });
  }, []);

  return (
    isLoading ? <span className="float-right spinner-grow spinner-grow-sm" role="status" aria-hidden="true" />
      : (
        <Fragment>
          <span className="mr-2">
            <DatasetCountBadge experimentData={expData} />
          </span>
          <span className="mr-2">
            <DatafileCountBadge experimentData={expData} />
          </span>
          <span className="mr-2">
            <ExperimentLastUpdatedBadge experimentData={expData} />
          </span>
          <span className="mr-2">
            <PublicAccessBadge experimentData={expData} />
          </span>
        </Fragment>
      )
  );
};

ExperimentViewPageBadges.propTypes = {
  experimentID: PropTypes.string.isRequired,
};

const elem = document.querySelector('.badges');
const experimentID = elem.id.split('-')[1];
ReactDOM.render(
  <ExperimentViewPageBadges experimentID={experimentID} />, elem,
);
