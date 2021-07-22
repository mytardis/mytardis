import React, { Fragment } from 'react';
import PropTypes from 'prop-types';

const Licenses = ({ licenses, onLicenseChange, selectedLicenseId }) => (
  <Fragment>
    {licenses.map(
      license => (
        <div className="license-option">
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
                disabled={license.id === selectedLicenseId}
              >
                {license.id === selectedLicenseId ? 'Selected' : 'Use'}
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

Licenses.defaultProps = {
  selectedLicenseId: null,
};
Licenses.propTypes = {
  onLicenseChange: PropTypes.func.isRequired,
  licenses: PropTypes.object.isRequired,
  selectedLicenseId: PropTypes.number,
};
export default Licenses;
