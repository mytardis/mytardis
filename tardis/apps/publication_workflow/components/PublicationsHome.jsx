import React, { Fragment } from 'react';
import PublicationButton from './PublicationButton';
import PublicationsList from './PublicationsList';
import FormModal from "./FormModal";

const PublicationsHome = () => (
  <Fragment>
    <FormModal />
    <PublicationsList />
  </Fragment>
);
export default PublicationsHome;
