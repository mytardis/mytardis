import React, { Fragment, useState } from 'react';
import Badge from 'react-bootstrap/Badge';
import PropTypes from 'prop-types';
import fetchExperimentData from './FetchData';

const DatasetCountBadge = ({ experimentID }) => {
  const [datasetCount, setDatasetCount] = useState('');

  React.useEffect(() => {
    fetchExperimentData(experimentID).then((data) => {
      const count = data.dataset_count;
      setDatasetCount(count);
    });
  }, []);


  return (
    <Fragment>
      <Badge variant="info">
        {datasetCount}
      </Badge>
    </Fragment>
  );
};

DatasetCountBadge.propTypes = {
  experimentID: PropTypes.string.isRequired,
};

export default DatasetCountBadge;
