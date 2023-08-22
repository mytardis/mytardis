import PropTypes from 'prop-types';
import React, { Fragment } from 'react';

const PublicationButton = ({ onclick, setViewType }) => (
  <Fragment>
    <div className="row">
      <div className="col-md-12 pull-right">
        <button
          type="button"
          className="btn btn-primary btn-lg mb-2 ms-2 pull-right"
          onClick={onclick}
        >
          <i className="fa fa-plus me-2" />
          Create publication
        </button>
        <div className="pull-right btn-group btn-lg">
          <button
            type="button"
            id="list"
            className="btn btn-secondary"
            onClick={setViewType}
          >
            <i className="fa fa-th-list me-2" />
            List
          </button>
          <button
            type="button"
            id="grid"
            className="btn btn-secondary"
            onClick={setViewType}
          >
            <i className="fa fa-th me-2" />
            Grid
          </button>
        </div>
      </div>
    </div>
  </Fragment>
);
export default PublicationButton;

PublicationButton.propTypes = {
  onclick: PropTypes.func.isRequired,
  setViewType: PropTypes.func.isRequired,
};
