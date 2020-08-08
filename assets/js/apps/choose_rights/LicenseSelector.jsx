import React, { Fragment, useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { fetchLicenses } from './FetchData';


const LicenseSelector = ({
  selectedAccessTypeId, currentLicense, onLicenseChange, selectedLicense, currentAccessTypeId,
}) => {
  const [licenses, setLicenses] = useState([]);
  useEffect(() => {
    fetchLicenses(selectedAccessTypeId).then((result) => { setLicenses(result); });
  }, [selectedAccessTypeId]);
  if (selectedLicense === currentLicense) {
    return (
      <Fragment>
        {licenses.map(
          license => (
            <div className="license-option form-group">
              <div className="row">
                <div className="col-md-2">
                  <input
                    type="hidden"
                    className="license-id"
                    value={license.id}
                  />
                  <button
                    type="button"
                    className="use-button btn btn-info"
                    title="Use"
                    value={license.id}
                    onClick={onLicenseChange}
                    disabled={license.id === currentLicense
                    || (currentAccessTypeId === selectedAccessTypeId)}
                  >
                    {license.id === currentLicense || (currentAccessTypeId === selectedAccessTypeId) ? 'Selected' : 'Use'}
                  </button>
                </div>
                <div className="col-md-10">
                  <div className="row">
                    <div className="col-md-9">
                      <h4 style={{ display: 'inline-block' }}>
                        <a target="_blank" rel="noreferrer" href={license.url}>{license.name}</a>
                      </h4>
                      <p>{license.internal_description}</p>
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
              </div>
            </div>
          ),
        )}
      </Fragment>
    );
  }
  return (
    <Fragment>
      {licenses.map(
        (license) => {
          if (license.id.toString() === selectedLicense) {
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
    </Fragment>
  );
};

LicenseSelector.propTypes = {
  selectedAccessTypeId: PropTypes.number.isRequired,
  currentLicense: PropTypes.number.isRequired,
  onLicenseChange: PropTypes.func.isRequired,
  selectedLicense: PropTypes.number.isRequired,
  currentAccessTypeId: PropTypes.string.isRequired,
};

export default LicenseSelector;
