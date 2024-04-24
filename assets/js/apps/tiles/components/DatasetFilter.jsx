import React, { Fragment } from 'react';
import PropTypes from 'prop-types';

const DatasetFilter = ({ onFilter, onSort }) => {
  const dropDOwnStyle = {
    minWidth: 'max-content',
    transform: 'translate3d(0px 38px 0px)',
  };
  const sortButtonStyle = {
    backgroundColor: 'transparent',
    border: 'none',
    cursor: 'pointer',
    textDecoration: 'underline',
    display: 'inline',
    margin: 0,
    padding: 0,
    color: 'blue',
  };
  return (
    <Fragment>
      <p>
        <div className="row">
          <div className="form-horizontal col-md-8">
            <div className="form-group has-search">
              {/* <span className="fa fa-search form-control-feedback"/> */}
              <input
                type="text"
                className="form-control"
                placeholder="Just start typing to filter datasets based on description"
                onKeyUp={onFilter}
              />
            </div>
          </div>
          <div className="form-horizontal col-md-4">
            <div className="btn-group">
              <button type="button" className="btn btn-outline-secondary float-end">Sort by</button>
              <button
                type="button"
                className="btn btn-outline-secondary dropdown-toggle dropdown-toggle-split"
                data-bs-toggle="dropdown"
                aria-haspopup="true"
                aria-expanded="false"
              >
                <span className="sr-only">Toggle Dropdown</span>
              </button>
              <div className="dropdown-menu" style={dropDOwnStyle} ref={(node) => { if (node) { node.style.setProperty('transform', 'translate3d(0px 38px 0px)', '!important'); } }}>
                <div className="row">
                  <div className="col col-md-8">
                    <span className="dropdown-item" href="#">
                      Description
                    </span>
                  </div>
                  <div className="col col-md-4">
                    <button className="fa fa-sort-alpha-asc mr-2 mt-2" style={sortButtonStyle} type="button" onClick={() => onSort('description', 'asc')} />
                    <button className="fa fa-sort-alpha-desc mt-2" type="button" style={sortButtonStyle} onClick={() => onSort('description', 'desc')} />
                  </div>
                </div>
                <div className="row">
                  <div className="col col-md-8">
                    <span className="dropdown-item" href="#">
                      DataFile count
                    </span>
                  </div>
                  <div className="col col-md-4">
                    <button className="fa fa-sort-numeric-asc mr-2 mt-2" type="button" style={sortButtonStyle} onClick={() => onSort('datafileCount', 'asc')} />
                    <button className="fa fa-sort-numeric-desc mt-2" type="button" style={sortButtonStyle} onClick={() => onSort('datafileCount', 'desc')} />
                  </div>
                </div>
                <div className="row">
                  <div className="col col-md-8">
                    <span className="dropdown-item" href="#">
                      Dataset size
                    </span>
                  </div>
                  <div className="col col-md-4">
                    <button className="fa fa-sort-numeric-asc mr-2 mt-2" type="button" style={sortButtonStyle} onClick={() => onSort('datasetSize', 'asc')} />
                    <button className="fa fa-sort-numeric-desc mt-2" type="button" style={sortButtonStyle} onClick={() => onSort('datasetSize', 'desc')} />
                  </div>
                </div>
                <div className="row">
                  <div className="col col-md-8">
                    <span className="dropdown-item" href="#">
                      Dataset modified time
                    </span>
                  </div>
                  <div className="col col-md-4">
                    <button className="fa fa-sort-numeric-asc mr-2 mt-2" type="button" style={sortButtonStyle} onClick={() => onSort('datasetTime', 'asc')} />
                    <button className="fa fa-sort-numeric-desc mt-2" type="button" style={sortButtonStyle} onClick={() => onSort('datasetTime', 'desc')} />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </p>
    </Fragment>
  );
};

DatasetFilter.propTypes = {
  onFilter: PropTypes.func.isRequired,
  onSort: PropTypes.func.isRequired,
};

export default DatasetFilter;
