import React from 'react';
import PropTypes from 'prop-types';

const Container = ({
  style, decorators, onClick, node, onSelect,
}) => {
  const iconType = node.toggled ? 'folder-open' : 'folder';
  const iconClass = node.children ? iconType : 'file-text';
  return (
    // eslint-disable-next-line jsx-a11y/no-static-element-interactions
    <div onClick={onClick} onKeyDown={onClick}>
      <decorators.Header
        node={node}
        style={style.header}
        iconClass={iconClass}
        onSelect={onSelect}
      />
    </div>
  );
};

Container.propTypes = {
  onSelect: PropTypes.func.isRequired,
  node: PropTypes.object.isRequired,
  style: PropTypes.object.isRequired,
  decorators: PropTypes.object.isRequired,
  onClick: PropTypes.func.isRequired,
};

export default Container;
