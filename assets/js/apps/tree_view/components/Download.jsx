import React, { Fragment, useState } from 'react';
import PropTypes from 'prop-types';

const FileDownloadButton = ({ href }) => (
  <Fragment>
    <a className="btn-sm" style={{ color: 'Black' }} title="Download" href={href}>
      <i className="fa fa-download fa-sm" />
    </a>
  </Fragment>
);

const TreeDownloadButton = ({ count }) => {
  const [buttonText, setButtonText] = useState('Select All');
  if (count > 0) {
    setButtonText('Download selected');
  }
  return (
    <Fragment>
      <button
        className="btn btn-outline-secondary"
        style={{ marginBottom: '12px', fontWeight: 'bold' }}
        title="Download"
        type="submit"
        count={count}
      >
        <i className="fa fa-download fa-sm mr-1 " />
        {buttonText}
      </button>
    </Fragment>
  );
};

FileDownloadButton.propTypes = {
  href: PropTypes.string.isRequired,
};
TreeDownloadButton.propTypes = {
  count: PropTypes.number.isRequired,
};

export { FileDownloadButton, TreeDownloadButton };
