import React, { Fragment, useState } from 'react';
import { css } from '@emotion/core';
import PropTypes from 'prop-types';
import { fetchExperimentData } from '../badges/components/utils/FetchData';
import Spinner from '../badges/components/utils/Spinner';


const CurrentLicense = ({ experimentId, licenseUpdatedCount }) => {
  const [expData, setExpData] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const spinnerCss = css`
    margin: auto;
    width: 20%;
    float: right;
    color: 9B9B9B;
  `;
  React.useEffect(() => {
    fetchExperimentData(experimentId).then((data) => {
      setExpData(data);
      setIsLoading(false);
    });
  }, [experimentId, licenseUpdatedCount]);
  return (
    isLoading ? <Spinner override={spinnerCss} />
      : (
        <Fragment>
          {expData.license ? (
            <Fragment>
              <div className="row">
                <div className="col-md-6">
                  This {expData.is_publication ? 'publication' : 'experiment'} data is licensed under
                  <a
                    rel="license"
                    property="dc:license"
                    href={expData.license.url}
                  >
                    {' '}
                    {expData.license.name}
                  </a>
                  .
                </div>
                { expData.license.image_url
                  ? (
                    <Fragment>
                      <div className="col-md-6">
                        <img src={expData.license.image_url} alt="" />
                      </div>
                    </Fragment>
                  )
                  : null}
              </div>
            </Fragment>
          ) : (
            <Fragment>
              <abbr title="All rights reserved">
                Unspecified
              </abbr>
            </Fragment>
          )}
        </Fragment>
      )
  );
};

CurrentLicense.propTypes = {
  experimentId: PropTypes.number.isRequired,
  licenseUpdatedCount: PropTypes.number.isRequired,
};

export default CurrentLicense;
