import React, { Fragment, useState } from 'react';
import ReactDOM from 'react-dom';

import PropTypes from 'prop-types';
import ExperimentLastUpdatedBadge from './ExperimentLastUpdateBadge';
import PublicAccessBadge from './PublicAccessBadge';
import DatasetCountBadge from './DatasetCountBadge';
import DatafileCountBadge from './DatafileCountBadge';
import fetchExperimentData from './utils/FetchData';
import Spinner from "./utils/Spinner";


const IndexPageBadges = ({ experimentID }) => {
  const [expData, setExpData] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  React.useEffect(() => {
    fetchExperimentData(experimentID).then((data) => {
      setExpData(data);
      setIsLoading(false);
    });
  }, []);
  return (
    isLoading ? <Spinner />
      : (
        <Fragment>
          <ul className="list-inline float-right list-unstyled">
            <li className="mr-1 list-inline-item">
              <ExperimentLastUpdatedBadge experimentData={expData} />
            </li>
            <li className="mr-1 list-inline-item">
              <DatasetCountBadge experimentData={expData} />
            </li>
            <li className="mr-1 list-inline-item">
              <DatafileCountBadge experimentData={expData} />
            </li>
            <li className="mr-1 list-inline-item">
              <PublicAccessBadge experimentData={expData} />
            </li>
          </ul>
        </Fragment>
      )
  );
};

IndexPageBadges.propTypes = {
  experimentID: PropTypes.string.isRequired,
};

document.querySelectorAll('.badges')
  .forEach((domContainer) => {
    const experimentID = domContainer.id.split('-')[1];
    ReactDOM.render(
      <IndexPageBadges experimentID={experimentID} />, domContainer,
    );
  });
