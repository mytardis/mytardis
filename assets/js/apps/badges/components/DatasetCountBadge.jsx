import React, { Fragment, useState } from 'react';
import Badge from 'react-bootstrap/Badge';
import PropTypes from 'prop-types';
import pluralize from 'pluralize';

const DatasetCountBadge = ({ experimentData }) => {
  const [datasetCount, setDatasetCount] = useState('');
  const [title, setTitle] = useState('');

  React.useEffect(() => {
    const count = experimentData.dataset_count;
    setDatasetCount(count);
    setTitle(`${count} ${pluralize('dataset', count)}`);
  }, []);


  return (
    <Fragment>
      <Badge bg="info" title={title}>
        <i className="fa fa-folder" />
        &nbsp;
        {datasetCount}
      </Badge>
    </Fragment>
  );
};

DatasetCountBadge.propTypes = {
  experimentData: PropTypes.object.isRequired,
};

export default DatasetCountBadge;
