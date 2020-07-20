import React, { Fragment } from 'react';
import ReactDOM from 'react-dom';
import Cookies from 'js-cookie';
import LicenseModal from './modal';

const content = document.getElementsByClassName('choose-rights')[0];
const experimentId = content.id.split('-')[2];

ReactDOM.render(
  <Fragment>
    <button
      className="public_access_button btn btn-outline-secondary btn-sm"
      data-toggle="modal"
      data-target="#modal-public-access"
      title="Change"
      type="submit"
    >
      <i className="fa fa-cog mr-1" />
      Change Public Access
    </button>
    <LicenseModal experimentId={experimentId} />
  </Fragment>, content,
);
