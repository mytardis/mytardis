import React, { Fragment, useState } from 'react';
import ReactDOM from 'react-dom';
import LicenseModal from './modal';
import ShareTabBadge from '../badges/components/ShareTabBadge';
import CurrentLicense from './CurrentLicense';
import ExperimentViewPageBadges from '../badges/components/ExperimentViewPageBadges';

const modalContainer = document.getElementsByClassName('choose-rights')[0];
const experimentId = parseInt(modalContainer.id.split('-')[2]);
const badgeContainer = document.getElementsByClassName('public-content')[0];
const headerBadgeContainer = document.querySelector('.badges');


const App = () => {
  const [licenseUpdatedCount, setLicenseUpdatedCount] = useState(0);
  const onLicenseUpdate = () => {
    setLicenseUpdatedCount(licenseUpdatedCount + 1);
  };
  return (
    <Fragment>
      <span>
        <dl>
          <dt>Current Public Access Settings</dt>
          <dd>
            <ShareTabBadge licenseUpdatedCount={licenseUpdatedCount} experimentID={experimentId} />
          </dd>
        </dl>
        <dl>
          <dt>Current License</dt>
          <dd>
            <CurrentLicense experimentId={experimentId} licenseUpdatedCount={licenseUpdatedCount} />
          </dd>
        </dl>
      </span>
      <LicenseModal
        container={modalContainer}
        experimentId={experimentId}
        onLicenseUpdate={onLicenseUpdate}
      />
      <ExperimentViewPageBadges
        experimentID={experimentId}
        container={headerBadgeContainer}
        licenseUpdatedCount={licenseUpdatedCount}
      />
    </Fragment>
  );
};

ReactDOM.render(<App />, badgeContainer);
