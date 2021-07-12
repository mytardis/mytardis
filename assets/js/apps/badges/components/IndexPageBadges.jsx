import React, { Fragment, useState } from 'react';
import ReactDOM from 'react-dom';

import PropTypes from 'prop-types';
import { css } from '@emotion/core';
import ExperimentLastUpdatedBadge from './ExperimentLastUpdateBadge';
import PublicAccessBadge from './PublicAccessBadge';
import DatasetCountBadge from './DatasetCountBadge';
import DatafileCountBadge from './DatafileCountBadge';
import { fetchExperimentData } from './utils/FetchData';
import Spinner from './utils/Spinner';


const IndexPageBadges = ({ experimentID }) => {
  const [expData, setExpData] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const spinnerCss = css`
    margin: auto;
    width: 20%;
    float: right;
    color: 9B9B9B;
  `;
  React.useEffect(() => {
    fetchExperimentData(experimentID).then((data) => {
      setExpData(data);
      setIsLoading(false);
    });
  }, []);
  return (
    isLoading ? <Spinner override={spinnerCss} />
      : (
        <Fragment>
          <ul className="list-inline float-end list-unstyled">
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

export default IndexPageBadges;
