import React, { Fragment } from 'react';
import PublicationCard from './PublicationCard';


const PublicationsList = () => (
  <Fragment>
    <div className="row">
      <div className="col-md-12">
        <button type="button" className="btn btn-primary btn-lg pull-right mb-2">
          <i className="fa fa-plus mr-2" />
          Create publication
        </button>
      </div>

    </div>
    <div className="row">
      <div className="row row-cols-1 row-cols-md-3 row-cols-lg-4 row-cols-xl-5">
        <PublicationCard publicationType="draft" />
        <PublicationCard publicationType="released" />
        <PublicationCard publicationType="draft" />
        <PublicationCard publicationType="retracted" />
        <PublicationCard publicationType="draft" />
        <PublicationCard publicationType="scheduled" />
        <PublicationCard publicationType="draft" />
        <PublicationCard />
      </div>
    </div>

  </Fragment>
);
export default PublicationsList;
