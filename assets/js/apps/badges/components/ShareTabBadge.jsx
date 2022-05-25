import React, { Fragment, useState } from 'react';

import PropTypes from 'prop-types';
import { css } from '@emotion/core';
import PublicAccessBadge from './PublicAccessBadge';
import { fetchExperimentData } from './utils/FetchData';
import Spinner from './utils/Spinner';

const ShareTabBadge = ({ experimentID, licenseUpdatedCount }) => {
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
  }, [experimentID, licenseUpdatedCount]);
  return (
    isLoading ? <Spinner override={spinnerCss} />
      : (
        <Fragment>
          <PublicAccessBadge experimentData={expData} />
        </Fragment>
      )
  );
};

ShareTabBadge.propTypes = {
  experimentID: PropTypes.number.isRequired,
  licenseUpdatedCount: PropTypes.number.isRequired,
};
export default ShareTabBadge;
