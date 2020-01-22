import React, { Fragment, useState } from 'react';
import Badge from 'react-bootstrap/Badge';
import PropTypes from 'prop-types';
import fetchExperimentData from './FetchData';

const PublicAccessBadge = ({ experimentID }) => {
  const [publicAccess, setPublicAccess] = useState('');
  const [title, setTitle] = useState('');
  const [variantType, setvariantType] = useState('');

  React.useEffect(() => {
    fetchExperimentData(experimentID).then((data) => {
      const accessType = data.public_access;
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
    });
  }, []);

  return (
    <Fragment>
      <Badge
        variant={variantType}
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
  experimentID: PropTypes.string.isRequired,
};

export default PublicAccessBadge;
