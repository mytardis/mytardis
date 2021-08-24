import React, { Fragment } from 'react';
import PropTypes from 'prop-types';


const AddDatasetButton = ({ experimentID }) => (
  /* TODO */
  /* {% if has_write_permissions and not experiment.is_publication %} */
  <Fragment>
    <a
      id="add-dataset"
      className="add-dataset btn btn-primary btn-sm float-end"
      href={`/experiment/${experimentID}/add-dataset`}
    >
      <i className="fa fa-plus" />
      Add New
    </a>
    <br />
  </Fragment>
);
AddDatasetButton.propTypes = {
  experimentID: PropTypes.string.isRequired,
};
export default AddDatasetButton;
