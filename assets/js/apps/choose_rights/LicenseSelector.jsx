import React, { Fragment, useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { fetchLicenses } from './FetchData';
import Licenses from './Licenses';


const LicenseSelector = ({
  selectedAccessTypeId, onLicenseChange,
  selectedLicense, showSelectedLicense, handleReselectChange,
}) => {
  const [licenses, setLicenses] = useState([]);
  useEffect(() => {
    fetchLicenses(selectedAccessTypeId).then((result) => { setLicenses(result); });
  }, [selectedAccessTypeId]);
  if (!showSelectedLicense) {
    return (
      <Licenses
        licenses={licenses}
        onLicenseChange={onLicenseChange}
        selectedLicenseId={selectedLicense || null}
      />
    );
  }
  return (
    <Fragment>
      {licenses.map(
        (license) => {
          if (license.id === selectedLicense) {
            return (
              <div id="selected-license-text">
                <div className="row">
                  <div className="col-md-9">
                    <h4 style={{ display: 'inline-block' }}>
                      <a target="_blank" rel="noreferrer" href={license.url}>
                        {license.name}
                      </a>
                    </h4>
                    <p>
                      {license.internal_description}
                    </p>
                  </div>
                  <div className="col-md-3">
                    <img
                      style={{ marginLeft: 'auto', marginRight: 'auto' }}
                      src={license.image_url}
                      alt=""
                    />
                  </div>
                </div>
              </div>
            );
          }
          return <Fragment />;
        },
      )}
      {/* eslint-disable-next-line react/button-has-type */}
      <button
        className="btn-secondary"
        id="reselect-license"
        onClick={handleReselectChange}
      >
        Reselect License
      </button>
    </Fragment>
  );
};

LicenseSelector.propTypes = {
  selectedAccessTypeId: PropTypes.number.isRequired,
  onLicenseChange: PropTypes.func.isRequired,
  selectedLicense: PropTypes.number,
  showSelectedLicense: PropTypes.bool.isRequired,
  handleReselectChange: PropTypes.func.isRequired,
};

export default LicenseSelector;
