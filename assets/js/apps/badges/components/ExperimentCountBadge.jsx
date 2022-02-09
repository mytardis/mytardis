import React, { Fragment, useState } from 'react';
import Badge from 'react-bootstrap/Badge';
import PropTypes from 'prop-types';
import pluralize from 'pluralize';

const ExperimentCountBadge = ({ projectData }) => {
  const [experimentCount, setExperimentCount] = useState('');
  const [title, setTitle] = useState('');

  React.useEffect(() => {
    const count = projectData.experiment_count;
    setExperimentCount(count);
    setTitle(`Related to ${count} ${pluralize('experiment', count)}`);
  }, []);


  return (
    <Fragment>
      <Badge variant="info" title={title}>
        <i className="fa fa-cogs" />
&nbsp;
        {experimentCount}
      </Badge>
    </Fragment>
  );
};

ExperimentCountBadge.propTypes = {
  projectData: PropTypes.object.isRequired,
};

export default ExperimentCountBadge;
