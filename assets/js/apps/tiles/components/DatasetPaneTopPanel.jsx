import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import DatasetCountHeader from './DatasetCountHeader';
import AddDatasetButton from './AddDatasetButton';
import DownloadButton from './DownloadButton';
import DatasetFilter from './DatasetFilter';

const DatasetPaneTopPanel = ({
  count, experimentID, selectedDatasets, csrfToken,
}) => (
  <Fragment>
    <DatasetCountHeader count={count} />
    <AddDatasetButton experimentID={experimentID} />
    <DownloadButton selectedDatasets={selectedDatasets} csrfToken={csrfToken} />
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
};
export default DatasetPaneTopPanel;
