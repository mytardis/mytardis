import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import pluralize from 'pluralize';

const DatasetCountHeader = ({ count }) => (
  <Fragment>
    <h3 style={{ display: 'inline' }}>
      {`${count}`}
      {' '}
      {pluralize('Dataset', count)}
    </h3>
  </Fragment>
);
DatasetCountHeader.propTypes = {
  count: PropTypes.number.isRequired,
};
export default DatasetCountHeader;
