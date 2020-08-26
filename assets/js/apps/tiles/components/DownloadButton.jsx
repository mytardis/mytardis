import React, { Fragment } from 'react';
import PropTypes from 'prop-types';

const DownloadButton = ({ selectedDatasets, csrfToken }) => (
  /* TODO */
  /* {% if has_write_permissions and not experiment.is_publication %} */
  <Fragment>
    <form method="POST" action="/download/datafiles/">
      {/* eslint-disable-next-line react/no-array-index-key */}
      {selectedDatasets.map((value, index) => <input type="hidden" key={index} name="dataset" value={value} />)}
      <input
        type="hidden"
        name="csrfmiddlewaretoken"
        value={csrfToken}
      />
      <input
        type="hidden"
        name="expid"
        value="82"
      />
      <input
        type="hidden"
        name="comptype"
        value="tar"
      />
      <input
        type="hidden"
        name="organization"
        value="deep-storage"
      />
      <button
        type="submit"
        value="submit"
        className="btn btn-outline-secondary btn-sm download-selected"
      >
        <i className="fa fa-download" />
        Download Selected
      </button>
    </form>
  </Fragment>
);
DownloadButton.propTypes = {
  selectedDatasets: PropTypes.array.isRequired,
  csrfToken: PropTypes.string.isRequired,
};
export default DownloadButton;
