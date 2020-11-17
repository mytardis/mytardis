import React, { Fragment } from 'react';
import PropTypes from 'prop-types';

const DatasetFilter = ({ onFilter }) => (
  <Fragment>
    <p>
      <div className="form-horizontal">
        <div className="form-group" style={{ margin: 0, padding: '10px 0 5px 10px', border: '1px solid #DDDDDD' }}>
          <div className="col-md-12" style={{ marginLeft: 0, marginBottom: '10px' }}>
            <input
              id="dataset-filter-text-{{cid}}"
              className="input-xlarge"
              type="text"
              style={{ width: '95%' }}
              placeholder="Just start typing to filter datasets based on descriptions"
              autoComplete="off"
              onKeyUp={onFilter}
            />
          </div>
        </div>
      </div>
    </p>
  </Fragment>
);

DatasetFilter.propTypes = {
  onFilter: PropTypes.func.isRequired,
};

export default DatasetFilter;
