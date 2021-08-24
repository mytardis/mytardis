import React, { Fragment, useState } from 'react';
import Badge from 'react-bootstrap/Badge';
import PropTypes from 'prop-types';
import { fetchHSMDatasetData } from './utils/FetchData';

const HSMDataFileCountBadge = ({ datasetId }) => {
  const [onlineFilesCount, setOnlineFilesCount] = useState('');
  const [totalFileCount, setTotalFileCount] = useState('');

  React.useEffect(() => {
    fetchHSMDatasetData(datasetId).then((data) => {
      setOnlineFilesCount(data.online_files);
      setTotalFileCount(data.total_files);
    });
  });

  return (
    <Fragment>
      <Badge
        bg="info"
        title={`${onlineFilesCount} of ${totalFileCount} Files online`}
      >
        <i className="fa fa-file" />
        &nbsp;
        {totalFileCount}
      </Badge>
    </Fragment>
  );
};

HSMDataFileCountBadge.propTypes = {
  datasetId: PropTypes.number.isRequired,
};

export default HSMDataFileCountBadge;
