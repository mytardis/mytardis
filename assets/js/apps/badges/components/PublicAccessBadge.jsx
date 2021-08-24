import React, { Fragment, useState } from 'react';
import Badge from 'react-bootstrap/Badge';
import PropTypes from 'prop-types';

const PublicAccessBadge = ({ experimentData }) => {
  const [publicAccess, setPublicAccess] = useState('');
  const [title, setTitle] = useState('');
  const [variantType, setvariantType] = useState('');

  React.useEffect(() => {
    const accessType = experimentData.public_access;
    if (accessType === 1) {
      setPublicAccess(' Private');
      setTitle(' No public access');
      setvariantType('secondary');
    } else if (accessType === 100) {
      setPublicAccess(' Public');
      setTitle(' All data is public');
      setvariantType('success');
    } else if (accessType === 25) {
      setPublicAccess(' [PUBLICATION] Awaiting release');
      setTitle(' Under embargo and awaiting release');
      setvariantType('secondary');
    } else if (accessType === 50) {
      setPublicAccess(' Metadata');
      setTitle(' Only descriptions are public, not data');
      setvariantType('success');
    }
  }, [experimentData]);

  return (
    <Fragment>
      <Badge
        bg={variantType}
        content={title}
        title={title}
      >
        <i className={publicAccess === ' Public' ? 'fa fa-eye' : 'fa fa-eye-slash'} />
        {publicAccess}
      </Badge>
    </Fragment>
  );
};

PublicAccessBadge.propTypes = {
  experimentData: PropTypes.object.isRequired,
};

export default PublicAccessBadge;
