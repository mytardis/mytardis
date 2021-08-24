import React, { Fragment, useState } from 'react';
import Badge from 'react-bootstrap/Badge';
import PropTypes from 'prop-types';
import pluralize from 'pluralize';


const DatafileCountBadge = ({ experimentData }) => {
  const [datafileCount, setDataFileCount] = useState('');
  const [title, setTitle] = useState('');

  React.useEffect(() => {
    const count = experimentData.datafile_count;
    setDataFileCount(count);
    setTitle(`${count} ${pluralize('file', count)}`);
  }, [experimentData]);

  return (
    <Fragment>
      <Badge bg="info" title={title}>
        <i className="fa fa-file" />
        &nbsp;
        {datafileCount}
      </Badge>
    </Fragment>
  );
};

DatafileCountBadge.propTypes = {
  experimentData: PropTypes.object.isRequired,
};

export default DatafileCountBadge;
