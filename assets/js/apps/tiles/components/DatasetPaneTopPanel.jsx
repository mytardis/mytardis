import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import DatasetCountHeader from './DatasetCountHeader';
import AddDatasetButton from './AddDatasetButton';
import DownloadButton from './DownloadButton';
import DatasetFilter from './DatasetFilter';

const DatasetPaneTopPanel = ({
  count, experimentID, selectedDatasets, csrfToken, experimentPermissions,
}) => (
  <Fragment>
    <DatasetCountHeader count={count} />
    {(experimentPermissions.write_permissions && !experimentPermissions.is_publication) ? (
      <AddDatasetButton experimentID={experimentID} />
    ) : ''}
    {experimentPermissions.download_permissions ? (
      <DownloadButton selectedDatasets={selectedDatasets} csrfToken={csrfToken} />
    ) : ''}
    <DatasetFilter />
  </Fragment>
);

DatasetPaneTopPanel.defaultProps = {
  csrfToken: '',
};
DatasetPaneTopPanel.propTypes = {
  count: PropTypes.number.isRequired,
  experimentID: PropTypes.string.isRequired,
  selectedDatasets: PropTypes.array.isRequired,
  csrfToken: PropTypes.string,
  experimentPermissions: PropTypes.object.isRequired,
};
export default DatasetPaneTopPanel;
