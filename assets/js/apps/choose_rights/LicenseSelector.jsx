import React, { Fragment, useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { fetchLicenses } from './FetchData';


const LicenseSelector = ({ selectedAccessTypeId, currentLicense, onLicenseChange }) => {
  const [licenses, setLicenses] = useState([]);
  useEffect(() => {
    fetchLicenses(selectedAccessTypeId).then((result) => { setLicenses(result); });
  }, [selectedAccessTypeId]);
  return (
    <Fragment>
      {licenses.map(
        license => (
          <div className="license-option form-group">
            <div className="row">
              <div className="col-md-2">
                <input type="hidden" className="license-id" value={license.id} />
                <button
                  type="button"
                  className="use-button btn btn-info"
                  title="Use"
                  value={license.id}
                  onClick={onLicenseChange}
                  disabled={license.id === currentLicense || (license.id === '' && !currentLicense)}
                >
                  {license.id === currentLicense || (license.id === '' && !currentLicense) ? 'Selected' : 'Use'}
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
};

LicenseSelector.propTypes = {
  selectedAccessTypeId: PropTypes.number.isRequired,
  currentLicense: PropTypes.number.isRequired,
  onLicenseChange: PropTypes.func.isRequired,
};

export default LicenseSelector;
