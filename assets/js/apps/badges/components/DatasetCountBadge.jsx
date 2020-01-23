import React, { Fragment, useState } from 'react';
import Badge from 'react-bootstrap/Badge';
import PropTypes from 'prop-types';
import pluralize from 'pluralize';
import fetchExperimentData from './utils/FetchData';

const DatasetCountBadge = ({ experimentID }) => {
  const [datasetCount, setDatasetCount] = useState('');
  const [title, setTitle] = useState('');

  React.useEffect(() => {
    fetchExperimentData(experimentID).then((data) => {
      const count = data.dataset_count;
      setDatasetCount(count);
      setTitle(`${count} ${pluralize('dataset', count)}`);
    });
  }, []);


  return (
    <Fragment>
      <Badge variant="info" title={title}>
        <i className="fa fa-folder" />
&nbsp;
        {datasetCount}
      </Badge>
    </Fragment>
  );
};

DatasetCountBadge.propTypes = {
  experimentID: PropTypes.string.isRequired,
};

export default DatasetCountBadge;
