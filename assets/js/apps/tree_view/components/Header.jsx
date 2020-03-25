import React from 'react';
import PropTypes from 'prop-types';
import { FileDownloadButton } from './Download';

const Header = ({
  onSelect, node, style, iconClass,
}) => {
  const iconStyle = { marginRight: '5px', opacity: '0.6' };
  let isDisabled = false;
  if (!node.children && !node.verified) {
    isDisabled = true;
  }
  return (
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
          ? <FileDownloadButton href={`/api/v1/dataset_file/${node.id}/download/`} isDisabled={isDisabled} /> : ''}
      </div>
    </div>
  );
};


Header.propTypes = {
  onSelect: PropTypes.func.isRequired,
  node: PropTypes.object.isRequired,
  style: PropTypes.object.isRequired,
  iconClass: PropTypes.string.isRequired,
};

export default Header;
