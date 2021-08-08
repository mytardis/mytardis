import React, { Fragment, useState } from 'react';
import Badge from 'react-bootstrap/Badge';
import PropTypes from 'prop-types';
import pluralize from 'pluralize';

const DatasetExperimentCountBadge = ({ datasetData }) => {
  const [count, setCount] = useState('');
  const [title, setTitle] = useState('');

  React.useEffect(() => {
    const datasetExperimentCount = datasetData.dataset_experiment_count;
    setCount(datasetExperimentCount);
    setTitle(`In ${count} ${pluralize('experiment', count)}`);
  });

  return (
    <Fragment>
      <Badge variant="info" title={title}>
        <i className="fa fa-cogs" />
&nbsp;
        {count}
      </Badge>
    </Fragment>
  );
};

DatasetExperimentCountBadge.propTypes = {
  datasetData: PropTypes.object.isRequired,
};

export default DatasetExperimentCountBadge;
