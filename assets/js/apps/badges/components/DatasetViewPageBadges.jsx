import React, { Fragment, useState } from 'react';
import ReactDOM from 'react-dom';
import PropTypes from "prop-types";
import { fetchDatasetData } from "./utils/FetchData";
import Spinner from "./utils/Spinner";
import DatasetSizeBadge from "./DatasetSizeBadge";
import DatasetExperimentCountBadge from "./DatasetExperimentCountBadge";
import DatasetDatafileCountBadge from "./DatasetDatafileCountBadge";


const DatasetViewPageBadges = ({ datasetID }) => {
  const [datasetData, setDatasetData] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  React.useEffect(() => {
    fetchDatasetData(datasetID).then((data) => {
      setDatasetData(data);
      setIsLoading(false);
    });
  }, []);

  return (
    isLoading ? <Spinner />
      : (
        <Fragment>
          <span className="mr-2">
            <DatasetExperimentCountBadge datasetData={datasetData} />
          </span>
          <span className="mr-2">
            <DatasetDatafileCountBadge datasetData={datasetData} />
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
const datasetID = elem.id.split('-')[1];

ReactDOM.render(
  <DatasetViewPageBadges datasetID={datasetID} />, elem,
);
