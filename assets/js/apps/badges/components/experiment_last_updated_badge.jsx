import React, { useEffect, useState } from 'react';

import Badge from 'react-bootstrap/Badge';
import PropTypes from 'prop-types';
import { fetchExperimentData } from './FetchData';

const ExperimentLastUpdatedBadge = ({ experimentID }) => {
  const [lastUpdatedTime, setLastUpdatedTime] = useState('');

  useEffect(() => {
    fetchExperimentData(experimentID).then((data) => {
      setLastUpdatedTime(new Date(data.update_time).toDateString());
    });
  }, []);
  return (
    <Badge variant="info" content="test" title="test">
      <i className="fa fa-clock-o" />
&nbsp;
      {lastUpdatedTime}
    </Badge>
  );
};

ExperimentLastUpdatedBadge.propTypes = {
  experimentID: PropTypes.string.isRequired,
};
export default ExperimentLastUpdatedBadge;
