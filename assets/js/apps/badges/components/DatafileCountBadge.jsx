import React, { Fragment, useState } from 'react';
import Badge from 'react-bootstrap/Badge';
import PropTypes from 'prop-types';
import fetchExperimentData from './utils/FetchData';
import pluralize from 'pluralize'

const DatafileCountBadge = ({experimentID}) => {
  const [datafileCount, setDataFileCount] = useState('');
  const [title, setTitle] = useState('');

  React.useState(() => {
    fetchExperimentData(experimentID).then((data) => {
      const count = data.datafile_count;
      setDataFileCount(count);
      setTitle(count+ ' ' + pluralize('file', count))
    });
  }, []);

  return(
    <Fragment>
      <Badge variant={'info'} title={title}>
        <i className={'fa fa-file'}/>&nbsp;
        {datafileCount}
      </Badge>
    </Fragment>
  )
};

DatafileCountBadge.propTypes = {
  experimentID: PropTypes.string.isRequired,
};

export default DatafileCountBadge;