import React, { Fragment, useState } from 'react';
import moment from 'moment';
import Badge from 'react-bootstrap/Badge';
import PropTypes from 'prop-types';
import { naturalDay } from './utils/humanize';

const ExperimentLastUpdatedBadge = ({ experimentData }) => {
  const [loading, setLoading] = useState(true);
  const [lastUpdatedTime, setLastUpdatedTime] = useState('');
  const [title, setTitle] = useState('');

  React.useEffect(() => {
    const date = new Date(experimentData.update_time);
    setLastUpdatedTime(naturalDay(date));
    setTitle(`Last updated: ${moment(date, 'DD-MM-YYYY').format('llll')}`);
    setLoading(false);
  }, [experimentData]);
  return (
    <Fragment>
      {loading
        ? <span className="float-end spinner-grow spinner-grow-sm" role="status" aria-hidden="true" />
        : (
          <Badge bg="info" title={title}>
            <i className="fa fa-clock-o" />
            &nbsp;
            {lastUpdatedTime}
          </Badge>
        )
        }
    </Fragment>

  );
};

ExperimentLastUpdatedBadge.propTypes = {
  experimentData: PropTypes.object.isRequired,
};
export default ExperimentLastUpdatedBadge;
