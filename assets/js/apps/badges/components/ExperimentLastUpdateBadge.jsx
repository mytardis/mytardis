import React, { Fragment, useState } from 'react';
import moment from 'moment';
import Badge from 'react-bootstrap/Badge';
import PropTypes from 'prop-types';
import fetchExperimentData from './utils/FetchData';
import { naturalDay } from './utils/humanize';

const ExperimentLastUpdatedBadge = ({ experimentID }) => {
  const [loading, setLoading] = useState(true);
  const [lastUpdatedTime, setLastUpdatedTime] = useState('');
  const [content, setContent] = useState('');
  const [title, setTitle] = useState('');

  React.useEffect(() => {
    fetchExperimentData(experimentID).then((data) => {
      const date = new Date(data.update_time);
      setLastUpdatedTime(naturalDay(date));
      setContent(date.toISOString());
      setTitle(`Last updated: ${moment(date, 'DD-MM-YYYY').format('llll')}`);
      setLoading(false);
    });
  }, []);
  return (
    <Fragment>
      {loading
        ? <span className="spinner-grow spinner-grow-sm" role="status" aria-hidden="true" />
        : (
          <Badge variant="info" content={content} title={title}>
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
  experimentID: PropTypes.string.isRequired,
};
export default ExperimentLastUpdatedBadge;
