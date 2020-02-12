import React, { Fragment } from 'react';
import PropTypes from 'prop-types';

const FileDownloadButton = ({ href }) => (
  <Fragment>
    <a className="btn-sm" style={{ color: 'Black' }} title="Download" href={href}>
      <i className="fa fa-download fa-sm" />
    </a>
  </Fragment>
);

const TreeDownloadButton = ({ count, onClick }) => (
  <Fragment>
    <form onSubmit={onClick}>
      <input
        type="hidden"
      />
      <input
        type="hidden"
        name="comptype"
        value="tar"
      />
      <input
        type="hidden"
        name="organization"
        value="deep-storage"
      />
      <button
        className="btn btn-outline-secondary"
        style={{ marginBottom: '12px', fontWeight: 'bold' }}
        title="Start selecting files to download"
        type="submit"
        value="submit"
      >
        <i className="fa fa-download fa-sm mr-1 " />
        {count > 0 ? 'Download Selected' : 'Select Files'}
        {count > 0 ? <span className="badge badge-light ml-1">{count}</span> : ''}
      </button>
    </form>

  </Fragment>
);

FileDownloadButton.propTypes = {
  href: PropTypes.string.isRequired,
};
TreeDownloadButton.propTypes = {
  count: PropTypes.number.isRequired,
  onClick: PropTypes.func.isRequired,
};

export { FileDownloadButton, TreeDownloadButton };
