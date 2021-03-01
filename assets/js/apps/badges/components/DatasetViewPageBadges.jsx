import React, { Fragment, useState } from 'react';
import ReactDOM from 'react-dom';
import PropTypes from 'prop-types';
import { css } from '@emotion/core';
import { fetchDatasetData } from './utils/FetchData';
import Spinner from './utils/Spinner';
import DatasetSizeBadge from './DatasetSizeBadge';
import DatasetExperimentCountBadge from './DatasetExperimentCountBadge';
import HSMDataFileCountBadge from './HSMDataFileCountBadge';


const DatasetViewPageBadges = ({ datasetID }) => {
  const [datasetData, setDatasetData] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const spinnerCss = css`
    margin: auto;
    width: 20%;
    float: right;
    color: 9B9B9B;
  `;
  React.useEffect(() => {
    fetchDatasetData(datasetID).then((data) => {
      setDatasetData(data);
      setIsLoading(false);
    });
  }, []);

  return (
    isLoading ? <Spinner override={spinnerCss} />
      : (
        <Fragment>
          <span className="mr-2">
            <DatasetExperimentCountBadge datasetData={datasetData} />
          </span>
          <span className="mr-2">
            {/* if HSM enabled */}
            <HSMDataFileCountBadge datasetId={datasetID} />
            {/* else DataFileCountBadge */}
          </span>
          <span className="mr-2">
            <DatasetSizeBadge datasetData={datasetData} />
          </span>
        </Fragment>
      )
  );
};

DatasetViewPageBadges.propTypes = {
  datasetID: PropTypes.string.isRequired,
};

const elem = document.querySelector('.badges');
let datasetID = null;
if (elem) {
  [, datasetID] = elem.id.split('-');
  ReactDOM.render(
    <DatasetViewPageBadges datasetID={datasetID} />, elem,
  );
}

export default DatasetViewPageBadges;
