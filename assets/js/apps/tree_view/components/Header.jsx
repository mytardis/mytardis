import React, { Fragment, useState } from 'react';
import PropTypes from 'prop-types';
import { saveAs } from 'file-saver';
import { FileDownloadButton } from './Download';
import { DownloadFile } from './Utils';

const Header = ({
  onSelect, node, style, iconClass,
}) => {
  const iconStyle = { marginRight: '5px', opacity: '0.6' };
  let isDisabled = false;
  const [isDownloading, setIsDownloading] = useState(false);
  if (!node.children && !node.verified) {
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
        data-toggle="tooltip"
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
          {isDisabled ? (
            <span style={{ color: 'red' }}>
              {node.name}
              (unverified)
            </span>
          ) : node.name}
          {iconClass === 'file-text'
            ? (
              <FileDownloadButton
                isDisabled={isDisabled}
                dataFileId={node.id}
                onClick={onClick}
                isDownloading={isDownloading}
              />
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
};

export default Header;
