import React, { Fragment } from 'react';
import PropTypes from 'prop-types';

const DownloadButton = ({ href }) => (
  <Fragment>
    <a className="btn btn-sm" title="Download" href={href}>
      <i className="fa fa-download fa-sm" />
    </a>
  </Fragment>
);

DownloadButton.propTypes = {
  href: PropTypes.string.isRequired,
};

export default DownloadButton;
