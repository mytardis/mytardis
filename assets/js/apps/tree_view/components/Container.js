import React from "react";
import PropTypes from "prop-types";

const Container = ({ style, decorators, terminal, onClick, node}) => {
    const iconClass = node.children ? (node.toggled ? 'folder-open' : 'folder'): 'file-text';
    return(
      <div onClick={onClick}>
        <decorators.Header node={node} style={style.header} iconClass={iconClass}/>
      </div>
    ) ;
};

Container.propTypes = {
    node: PropTypes.object,
    style: PropTypes.object,
    decorators: PropTypes.object,
    onClick: PropTypes.func
};

export default Container;