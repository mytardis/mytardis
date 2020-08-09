import React, { Fragment } from 'react';
import ReactDOM from 'react-dom';
import LicenseModal from './modal';

const content = document.getElementsByClassName('choose-rights')[0];
const experimentId = content.id.split('-')[2];
const badgeContainer = document.getElementsByClassName('public-badge')[0];

ReactDOM.render(
  <LicenseModal badgeContainer={badgeContainer} experimentId={experimentId} />,
  content,
);
