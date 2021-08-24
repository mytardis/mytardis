import React, { Fragment, useState } from 'react';
import fileSize from 'filesize';
import Badge from 'react-bootstrap/Badge';
import PropTypes from 'prop-types';

const ExperimentSizeBadge = ({ experimentData }) => {
  const [experimentSize, setExperimentSize] = useState('');
  const [title, setTitle] = useState('');

  React.useEffect(() => {
    let size = experimentData.experiment_size;
    size = fileSize(size, { base: 2 });
    setExperimentSize(size);
    setTitle(`Experiment size is ~ ${size}`);
  }, []);
  return (
    <Fragment>
      <Badge bg="info" title={title}>
        {experimentSize}
      </Badge>
    </Fragment>
  );
};

ExperimentSizeBadge.propTypes = {
  experimentData: PropTypes.object.isRequired,
};

export default ExperimentSizeBadge;
