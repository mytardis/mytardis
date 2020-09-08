import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import Spinner from '../../badges/components/utils/Spinner';
import { Button, OverlayTrigger, Tooltip } from 'react-bootstrap';
/** @jsx jsx */
import { jsx } from '@emotion/core';

const FileDownloadButton = ({ isDisabled, onClick, isDownloading }) => {
  const notActive = {
    pointerEvents: 'none',
    cursor: 'default',
    textDecoration: 'none',
    color: 'grey',
  };
  return (
    <Fragment>
      {/* eslint-disable-next-line jsx-a11y/anchor-is-valid,jsx-a11y/interactive-supports-focus */}
      <a
        className="btn-sm"
        style={isDisabled ? notActive : { color: 'black' }}
        onClick={onClick}
        title="Download"
        role="button"
        onKeyPress={onClick}
      >
        <i className="fa fa-download fa-sm" />
        {isDownloading ? <Spinner /> : ''}
      </a>
    </Fragment>
  );
};
const renderTooltip = props => (
  <Tooltip id="button-tooltip" {...props}>
    Request for Recall
  </Tooltip>
);
const handleRecallRequest = (event) => {
  event.preventDefault();
};
const FileRecallButton = ({ recallUrl }) => (
  <Fragment>
    <OverlayTrigger
      placement="top"
      delay={{ show: 250, hide: 400 }}
      overlay={renderTooltip}
    >
      <Button
        variant="outline-secondary"
        onClick={handleRecallRequest}
        css={{
          fontSize: '0.75rem', lineHeight: '0.25', padding: '0rem 0rem', margin: '0 10px 0 10px',
        }}
        type="button"
        data-recall-url={recallUrl}
      >
        <i className="fa fa-undo" css={{ marginLeft: '10px', marginRight: '10px' }} />
      </Button>
    </OverlayTrigger>
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
  isDisabled: PropTypes.bool.isRequired,
  onClick: PropTypes.func.isRequired,
  isDownloading: PropTypes.bool.isRequired,
};
TreeDownloadButton.propTypes = {
  count: PropTypes.number.isRequired,
  onClick: PropTypes.func.isRequired,
};
FileRecallButton.propTypes = {
  recallUrl: PropTypes.string,
};
FileRecallButton.defaultProps = {
  recallUrl: '',
};

export {
  FileDownloadButton, TreeDownloadButton, TreeSelectButton, FileRecallButton,
};
