import React, { Fragment, useState } from 'react';
import Badge from 'react-bootstrap/Badge';
import PropTypes from 'prop-types';
import pluralize from 'pluralize';

const DatasetDatafileCountBadge = ({ datasetData }) => {
  const [count, setCount] = useState('');
  const [title, setTitle] = useState('');

  React.useEffect(() => {
    const datasetDatafileCount = datasetData.dataset_datafile_count;
    setCount(datasetDatafileCount);
    setTitle(`${count} ${pluralize('file', count)}`);
  });

  return (
    <Fragment>
      <Badge bg="info" title={title}>
        <i className="fa fa-file" />
        &nbsp;
        {count}
      </Badge>
    </Fragment>
  );
};

DatasetDatafileCountBadge.propTypes = {
  datasetData: PropTypes.object.isRequired,
};

export default DatasetDatafileCountBadge;
