import React, { Fragment, useState } from 'react';
import { filesize } from 'filesize';
import Badge from 'react-bootstrap/Badge';
import PropTypes from 'prop-types';

const DatasetSizeBadge = ({ datasetData }) => {
  const [datasetSize, setDatasetSize] = useState('');
  const [title, setTitle] = useState('');

  React.useEffect(() => {
    let size = datasetData.dataset_size;
    size = filesize(size, { base: 2 });
    setDatasetSize(size);
    setTitle('Dataset size is');
  });

  return (
    <Fragment>
      <Badge variant="info" title={title}>
        {datasetSize}
      </Badge>
    </Fragment>
  );
};

DatasetSizeBadge.propTypes = {
  datasetData: PropTypes.object.isRequired,
};

export default DatasetSizeBadge;
