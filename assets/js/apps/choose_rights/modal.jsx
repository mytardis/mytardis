import React, { Fragment, useEffect, useState } from 'react';
import Cookies from 'js-cookie';
import PropTypes from 'prop-types';
import { createPortal } from 'react-dom';
import { fetchModalData } from './FetchData';
import LicenseSelector from './LicenseSelector';

const csrfToken = Cookies.get('csrftoken');
const LicenseModal = ({ experimentId, container, onLicenseUpdate }) => {
  const [modalData, setModalData] = useState([]);
  const [selectedAccessTypeId, setSelectedAccessTypeId] = useState(0);
  const [selectedLicenseId, setSelectedLicenseId] = useState(null);
  const [showMessage, setShowMessage] = useState(false);
  const [licenseUpdatedCount, setLicenseUpdatedCount] = useState(0);
  const [isrightsUpdated, setIsrightsUpdated] = useState(false);
  const [showSelectedLicense, setShowSelectedLicense] = useState(false);
  const [showLegalSection, setShowLegalSection] = useState(false);
  const [showButtons, setShowButtons] = useState(false);
  useEffect(() => {
    fetchModalData(experimentId).then((result) => {
      setModalData(result);
      setSelectedAccessTypeId(result.public_access);
      setSelectedLicenseId(result.license);
    });
  }, [experimentId]);

  const handleChange = (event) => {
    setShowLegalSection(false);
    setShowButtons(false);
    setShowMessage(false);
    setShowSelectedLicense(false);
    setSelectedAccessTypeId(event.target.value);
  };
  const handleReselectChange = (event) => {
    event.preventDefault();
    setShowSelectedLicense(false);
  };
  const handleSubmit = (event) => {
    event.preventDefault();
    /* action="/ajax/experiment/84/rights" */
    fetch(`/ajax/experiment/${experimentId}/rights`, {
      method: 'post',
      headers: {
        'Accept': 'application/json', // eslint-disable-line quote-props
        'Content-Type': 'application/json',
        'X-CSRFToken': Cookies.get('csrftoken'),
      },
      body: JSON.stringify({
        csrfmiddlewaretoken: Cookies.get('csrftoken'),
        license: selectedLicenseId.toString(),
        legal_text: modalData.legal_text,
        public_access: selectedAccessTypeId.toString(),
      }),
    }).then(
      (response) => {
        if (!response.ok) {
          setIsrightsUpdated(false);
          setShowMessage(true);
        }
        return response.json();
      },
    ).then(
      () => {
        setIsrightsUpdated(true);
        setShowMessage(true);
        setLicenseUpdatedCount(licenseUpdatedCount + 1);
        onLicenseUpdate();
      },
    );
  };
  const handleLicenseChange = (event) => {
    // if selected license is not null
    if (event.target.value === '') {
      setShowLegalSection(true);
      // display submit buttons
      setShowButtons(true);
      setShowSelectedLicense(true);
      setSelectedLicenseId('');
    } else {
      // display legal text
      setShowLegalSection(true);
      // display submit buttons
      setShowButtons(true);
      setShowSelectedLicense(true);
      setSelectedLicenseId(Number(event.target.value));
    }
  };

  return (
    <Fragment>
      {createPortal(
        <Fragment>
          <button
            className="public_access_button btn btn-outline-secondary btn-sm"
            data-bs-toggle="modal"
            data-bs-target="#modal-public-access"
            title="Change"
            type="submit"
          >
            <i className="fa fa-cog me-1" />
            Change Public Access
          </button>
          <div className="modal" id="modal-public-access" role="dialog" tabIndex="-1">
            <div className="modal-dialog modal-lg" role="document">
              <div className="modal-content">
                <div className="modal-header">
                  <h1 className="title">Public Access</h1>
                  <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div className="loading-placeholder" style={{ display: 'none' }}>
                  <p>
                    Please wait...
                  </p>
                </div>
                <div className="modal-body">
                  { showMessage
                    ? (
                      <div id="choose-rights-message">
                        {isrightsUpdated ? (
                          <div className="alert alert-success">
                            {/* eslint-disable-next-line jsx-a11y/anchor-is-valid */}
                            <a className="close" data-dismiss="alert">×</a>
                            <strong>Success!</strong>
                            <span> Licensing Changed.</span>
                          </div>
                        )
                          : (
                            <div className="alert alert-danger">
                              {/* eslint-disable-next-line jsx-a11y/anchor-is-valid */}
                              <a className="close" data-dismiss="alert">×</a>
                              <strong>Error! Something went wrong</strong>
                            </div>
                          )
                    }

                      </div>
                    ) : null
              }
                  <h3>Step 1: Change Public Access:</h3>
                  <br />
                  <form method="POST" onSubmit={handleSubmit} className="experiment-rights form-horizontal">
                    <input type="hidden" name="csrfmiddlewaretoken" value={csrfToken} />
                    <input type="hidden" name="license" value={selectedLicenseId} />
                    <input type="hidden" name="legal_text" value={modalData.legal_text} />
                    <div className="form-group">
                      <label className="col-form-label col-md-3 " htmlFor="id_public_access">Public access</label>
                      <div className="col-md-9 ">
                        <select
                          name="public_access"
                          className="form-control"
                          id="id_public_access"
                          value={selectedAccessTypeId}
                          onChange={handleChange}
                        >
                          <option value="1">No public access (hidden)</option>
                          <option value="25">Ready to be released pending embargo expiry</option>
                          <option value="50">Public Metadata only (no data file access)</option>
                          <option value="100">Public</option>
                        </select>
                      </div>
                    </div>

                    <h3>Step 2: Select a license:</h3>
                    <div id="license-options">
                      <LicenseSelector
                        selectedAccessTypeId={selectedAccessTypeId}
                        onLicenseChange={handleLicenseChange}
                        selectedLicense={selectedLicenseId}
                        showSelectedLicense={showSelectedLicense}
                        handleReselectChange={handleReselectChange}
                      />
                    </div>
                    <div id="selected-license-text" />
                    <div id="legal" style={{ display: !showLegalSection ? 'None' : 'block' }}>
                      <h3>Step 3: Accept The Legal Agreement:</h3>
                      <pre
                        id="publishing-legal-text"
                        style={{ whiteSpace: 'pre-wrap', wordBreak: 'keep-all' }}
                      >
                        { modalData.legal_text }
                      </pre>
                      <div className="checkbox">
                        <label>
                          <input id="publishing-consent" className="me-1" type="checkbox" required value="Agree" />
                          I agree to the above terms
                        </label>
                      </div>
                    </div>
                    <div id="confirm-license-btn-group" className="form-group text-right" style={{ display: showButtons ? 'block' : 'None' }}>
                      <button
                        type="button"
                        className="cancel-button btn btn-outline-secondary me-1"
                        data-dismiss="modal"
                      >
                        <i className="fa fa-close" />
                        Cancel
                      </button>
                      <button type="submit" className="submit-button btn btn-primary">
                        <i className="fa fa-check" />
                        Confirm
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            </div>
          </div>
        </Fragment>,
        container,
      )
      }
    </Fragment>
  );
};

LicenseModal.propTypes = {
  experimentId: PropTypes.number.isRequired,
  container: PropTypes.object.isRequired,
  onLicenseUpdate: PropTypes.func.isRequired,
};
export default LicenseModal;
