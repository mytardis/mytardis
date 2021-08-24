import React, { Fragment, useState } from 'react';
import PropTypes from 'prop-types';
import { saveAs } from 'file-saver';
import { DownloadFile } from './Utils';
import { FileDownloadButton, FileRecallButton } from './Download';

const Header = ({
  onSelect, node, style, iconClass, hsmEnabled,
}) => {
  const iconStyle = { marginRight: '5px', opacity: '0.6' };
  const dotStyleOnline = {
    height: '10px', width: '10px', backgroundColor: '#28a745', borderRadius: '50%', display: 'inline-block',
  };
  const dotStyleOffline = {
    height: '10px', width: '10px', backgroundColor: '#bbb', borderRadius: '50%', display: 'inline-block',
  };
  let isDisabled = false;
  const [isDownloading, setIsDownloading] = useState(false);
  if ((!node.children && !node.verified) || (!node.children && !node.is_online)) {
    isDisabled = true;
  }
  const onClick = () => {
    isDisabled = true;
    setIsDownloading(true);
    DownloadFile(node.id).then((resp) => {
      setIsDownloading(true);
      let fileName = '';
      const disposition = resp.headers.get('Content-Disposition');
      if (disposition && disposition.indexOf('attachment') !== -1) {
        const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
        const matches = filenameRegex.exec(disposition);
        if (matches != null && matches[1]) {
          fileName = matches[1].replace(/['"]/g, '');
        }
      }
      resp.blob().then((fileContent) => {
        saveAs(fileContent, fileName);
        setIsDownloading(false);
      });
    });
  };
  if (node.next_page) {
    return (
      <button
        type="button"
        className="btn btn-outline-secondary btn-sm"
        onClick={onSelect}
        data-bs-toggle="tooltip"
        data-placement="right"
        title={node.display_text}
      >
        Load more
      </button>
    );
  }
  return (
    <Fragment>
      <div style={style.base}>
        <div style={{ ...style.title }}>
          <input
            type="checkbox"
            className="datafile_checkbox"
            style={{ marginRight: '5px' }}
            onClick={onSelect}
            checked={node.selected}
            readOnly
            disabled={isDisabled}
          />
          <i className={`fa fa-${iconClass}`} style={iconStyle} />
          {/* eslint-disable-next-line no-nested-ternary */}
          {!node.verified && !node.children ? (
            <span style={{ color: 'red' }}>
              {node.name}
              (unverified)
            </span>
          ) : !node.is_online && !node.children ? (
            <span className="text-muted">
              {node.name}
              (archived)
            </span>
          ) : node.name}
          {iconClass === 'file-text'
            ? (
              <Fragment>
                {node.is_online
                  ? (
                    <FileDownloadButton
                      isDisabled={isDisabled}
                      dataFileId={node.id}
                      onClick={onClick}
                      isDownloading={isDownloading}
                    />
                  ) : ''
                  }
                {/* eslint-disable-next-line no-nested-ternary */}
                {hsmEnabled ? (
                  node.is_online ? (<span style={dotStyleOnline} title="online" />)
                    : (
                      <Fragment>
                        <FileRecallButton recallUrl={node.recall_url} />
                        <span style={dotStyleOffline} title="offline" />
                      </Fragment>
                    )
                ) : ''}
              </Fragment>

            ) : ''}
        </div>
      </div>
    </Fragment>
  );
};


Header.propTypes = {
  onSelect: PropTypes.func.isRequired,
  node: PropTypes.object.isRequired,
  style: PropTypes.object.isRequired,
  iconClass: PropTypes.string.isRequired,
  hsmEnabled: PropTypes.bool,
};
Header.defaultProps = {
  hsmEnabled: false,
};
export default Header;
