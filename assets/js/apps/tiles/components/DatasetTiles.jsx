import React, { Fragment } from 'react';
import DatasetTile from './DatasetTile';


const DatasetTiles = ({ data }) => {
  return (
    <Fragment>
      <ul className="datasets thumbnails">
        {data.map(
          (dataset, index) => (
            <DatasetTile data={dataset} key={dataset.id} index={index} />),
        )}
      </ul>
    </Fragment>
  );
};

export default DatasetTiles;
