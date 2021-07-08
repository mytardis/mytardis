import React, { Fragment } from 'react';

const PublicationButton = ({onclick}) => (
  <Fragment>
    <div className="row">
      <div className="col-md-12">
        <button type="button" className="btn btn-primary btn-lg pull-right mb-2" onClick={onclick}>
          <i className="fa fa-plus mr-2" />
          Create publication
        </button>
      </div>

    </div>
  </Fragment>
);
export default PublicationButton;