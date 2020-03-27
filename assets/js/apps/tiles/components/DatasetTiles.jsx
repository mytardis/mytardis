import React, { Fragment, useEffect, useState } from 'react';


const DatasetTiles = ({ experimentID }) => {
  const [data, setData] = useState([]);
  useEffect(() => {
    const datasetData = fetchExperimentDataset(experimentID);
    setData(datasetData);
  }, [experimentID]);
  return (
    <Fragment>
      {data.map(
        dataset => <DatasetTile data={dataset} />,
      )}
    </Fragment>
  );
};

export default DatasetTiles;
