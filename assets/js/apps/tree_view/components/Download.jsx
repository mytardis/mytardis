import { Fragment, useState } from 'react';
import PropTypes from 'prop-types';
import { Button, OverlayTrigger, Tooltip } from 'react-bootstrap';
/** @jsx jsx */
import { jsx } from '@emotion/react';
import Spinner from '../../badges/components/utils/Spinner';

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

const FileRecallButton = ({ recallUrl }) => {
  const [isDisabled] = useState(false);
  const [tooltipMessage, setToolTipMessage] = useState('Request Recall');
  const [buttonText, setButtonText] = useState('Request Recall');
  const [isLoading, setIsloading] = useState(false);
  const handleClick = () => {
    setIsloading(true);
    setButtonText('Requesting Recall');
    // console.log('clicked');
    // make a request for recall
    fetch(recallUrl, {
      method: 'get',
      headers: {
        'Accept': 'application/json', // eslint-disable-line quote-props
        'Content-Type': 'application/json',
      },
    }).then(responseJson => (responseJson.json()))
    // eslint-disable-next-line no-unused-vars
      .then((response) => {
        setToolTipMessage('Recall requested: You will be notified via '
          + 'email when recall is complete');
        setButtonText('Recall Requested');
        setIsloading(false);
      });
  };
  return (
    <Fragment>
      <OverlayTrigger
        placement="top"
        delay={{ show: 250, hide: 400 }}
        overlay={(
          <Tooltip id="button-tooltip">
            {tooltipMessage}
          </Tooltip>
)}
      >
        <Button
          variant="outline-secondary"
          onClick={handleClick}
          disabled={isDisabled}
          css={{
            fontSize: '0.75rem', lineHeight: '0.25', padding: '0rem 0rem', margin: '0 10px 0 10px',
          }}
          type="button"
          data-recall-url={recallUrl}
        >
          {buttonText}
          {isLoading ? <i className="fa fa-spinner fa-spin" css={{ marginLeft: '10px', marginRight: '10px' }} />
            : <i className="fa fa-undo" css={{ marginLeft: '10px', marginRight: '10px' }} />
            }
        </Button>
      </OverlayTrigger>
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
const TreeRecallButton = ({
  buttonText, onClick, disabled, recallTooltip,
}) => (
  <Fragment>
    <OverlayTrigger
      placement="top"
      delay={{ show: 250, hide: 1200 }}
      overlay={(
        <Tooltip id="button-tooltip">
          {recallTooltip}
        </Tooltip>
)}
    >
      <Button
        variant="outline-secondary"
        style={{
          marginBottom: '12px', fontWeight: 'bold', marginLeft: '2px', pointerEvents: disabled,
        }}
        type="submit"
        value="submit"
        onClick={onClick}
      >
        {buttonText}
      </Button>
    </OverlayTrigger>
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
TreeRecallButton.propTypes = {
  buttonText: PropTypes.string.isRequired,
  onClick: PropTypes.func.isRequired,
  disabled: PropTypes.string.isRequired,
  recallTooltip: PropTypes.string.isRequired,
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
  FileDownloadButton, TreeDownloadButton, TreeSelectButton, FileRecallButton, TreeRecallButton,
};
