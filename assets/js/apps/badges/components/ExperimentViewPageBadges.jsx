import React, { Fragment, useState } from 'react';
import { createPortal } from 'react-dom';
import PropTypes from 'prop-types';
import { css } from '@emotion/core';
import ExperimentLastUpdatedBadge from './ExperimentLastUpdateBadge';
import PublicAccessBadge from './PublicAccessBadge';
import DatasetCountBadge from './DatasetCountBadge';
import DatafileCountBadge from './DatafileCountBadge';
import { fetchExperimentData } from './utils/FetchData';
import Spinner from './utils/Spinner';
import ExperimentSizeBadge from './ExperimentSizeBadge';


const ExperimentViewPageBadges = ({ experimentID, container, licenseUpdatedCount }) => {
  const [expData, setExpData] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const spinnerCss = css`
    width: 20%;
    color: 9B9B9B;
    float: right;
  `;

  React.useEffect(() => {
    fetchExperimentData(experimentID).then((data) => {
      setExpData(data);
      setIsLoading(false);
    });
  }, [experimentID, licenseUpdatedCount]);

  return (
    <Fragment>
      {createPortal(
        isLoading ? (
          <Fragment>
            <Spinner override={spinnerCss} />
          </Fragment>
        )
          : (
            <Fragment>
              <span className="me-2">
                <DatasetCountBadge experimentData={expData} />
              </span>
              <span className="me-2">
                <DatafileCountBadge experimentData={expData} />
              </span>
              <span className="me-2">
                <ExperimentSizeBadge experimentData={expData} />
              </span>
              <span className="me-2">
                <ExperimentLastUpdatedBadge experimentData={expData} />
              </span>
              <span className="me-2">
                <PublicAccessBadge experimentData={expData} />
              </span>
            </Fragment>
          ), container,
      )
    }
    </Fragment>
  );
};

ExperimentViewPageBadges.propTypes = {
  experimentID: PropTypes.number.isRequired,
  licenseUpdatedCount: PropTypes.number.isRequired,
  container: PropTypes.object.isRequired,
};


export default ExperimentViewPageBadges;
