import React, { Fragment, useState } from 'react';
import ReactDOM from 'react-dom';
import PropTypes from 'prop-types';
import { css } from '@emotion/react';
import { fetchDatasetData } from './utils/FetchData';
import Spinner from './utils/Spinner';
import DatasetSizeBadge from './DatasetSizeBadge';
import DatasetExperimentCountBadge from './DatasetExperimentCountBadge';
import HSMDataFileCountBadge from './HSMDataFileCountBadge';
import DatafileCountBadge from './DatafileCountBadge';


const DatasetViewPageBadges = ({ datasetID, hsmEnabled }) => {
  const [datasetData, setDatasetData] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [experimentData, setExperimentData] = useState({});
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
      setExperimentData({ datafile_count: data.dataset_datafile_count });
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
            {hsmEnabled ? <HSMDataFileCountBadge datasetId={parseInt(datasetID, 10)} />
              : <DatafileCountBadge experimentData={experimentData} />
            }
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
  hsmEnabled: PropTypes.bool.isRequired,
};

const hsmElem = document.querySelector('#hsm-enabled');
let hsmEnabled = false;
if (hsmElem) {
  hsmEnabled = hsmElem.value === 'True';
}
const elem = document.querySelector('.badges');
let datasetID = null;
if (elem) {
  [, datasetID] = elem.id.split('-');
  ReactDOM.render(
    <DatasetViewPageBadges datasetID={datasetID} hsmEnabled={hsmEnabled} />, elem,
  );
}

export default DatasetViewPageBadges;
