import React, {useState} from 'react';
import PropTypes from 'prop-types';

const Header = ({ node, style, iconClass }) => {
    const [iconTypeClass, setIconTypeClass] = useState(iconClass);
    const iconStyle = {marginRight: '5px', opacity: '0.6'};
    return (
      <div style={style.base}>
        <div style={{ ...style.title }}>
            <i className={`fa fa-${iconTypeClass}`} style={iconStyle}/>
            {node.name}
        </div>
      </div>
    );
};


Header.propTypes = {
    node: PropTypes.object,
    style: PropTypes.object,
    iconClass: PropTypes.string
};

export default Header;
