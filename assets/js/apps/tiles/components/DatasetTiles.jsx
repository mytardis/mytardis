import React, { Fragment, useEffect, useState } from 'react';

import DatasetTile from './DatasetTile';
import fetchDatasetsForExperiment from './utils/FetchData';


const DatasetTiles = ({ experimentID }) => {
  const [data, setData] = useState([]);
  useEffect(() => {
    fetchDatasetsForExperiment(experimentID).then(result => setData(result));
  }, [experimentID]);
  return (
    <Fragment>
      <ul className="datasets thumbnails">
        {data.map(
          dataset => <DatasetTile data={dataset} key={dataset.id} />,
        )}
      </ul>
    </Fragment>
  );
};

export default DatasetTiles;
