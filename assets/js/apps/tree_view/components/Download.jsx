import React, { Fragment } from 'react';
import PropTypes from 'prop-types';

const FileDownloadButton = ({ href, isDisabled }) => {
  const notActive = {
    pointerEvents: 'none',
    cursor: 'default',
    textDecoration: 'none',
    color: 'grey',
  };
  return (
    <Fragment>
      <a className="btn-sm" style={isDisabled ? notActive : { color: 'black' }} title="Download" href={href}>
        <i className="fa fa-download fa-sm" />
      </a>
    </Fragment>
  );
};

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
        style={{ marginBottom: '12px', fontWeight: 'bold', marginRight: '2px' }}
        title={count > 0 ? `Download ${count} selected files/folders` : 'Start selecting files to download'}
        type="submit"
        value="submit"
        disabled={!(count > 0)}
      >
        <i className="fa fa-download fa-sm mr-1 " />
        {count > 0 ? 'Download Selected' : 'Select Files...'}
        {count > 0 ? <span className="badge badge-light ml-1">{count}</span> : ''}
      </button>
    </form>

  </Fragment>
);

const TreeSelectButton = ({ count, onClick, buttonText }) => (
  <Fragment>
    <button
      className="btn btn-outline-secondary"
      style={{ marginBottom: '12px', fontWeight: 'bold' }}
      title={count > 0 ? 'Select None' : 'Select All'}
      type="submit"
      value="submit"
      onClick={onClick}
    >
      {buttonText}
    </button>
  </Fragment>
);

TreeSelectButton.propTypes = {
  count: PropTypes.number.isRequired,
  onClick: PropTypes.func.isRequired,
  buttonText: PropTypes.string.isRequired,
};

FileDownloadButton.propTypes = {
  href: PropTypes.string.isRequired,
  isDisabled: PropTypes.bool.isRequired,
};
TreeDownloadButton.propTypes = {
  count: PropTypes.number.isRequired,
  onClick: PropTypes.func.isRequired,
};

export { FileDownloadButton, TreeDownloadButton, TreeSelectButton };
