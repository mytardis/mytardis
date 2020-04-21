import React, { Fragment } from 'react';
import DatasetTile from './DatasetTile';


const DatasetTiles = ({ data, listName }) => {
  console.log(listName);
  return (
    <Fragment>
      <ul className="datasets thumbnails">
        {data.map(
          (dataset, index) => (
            <DatasetTile data={dataset} key={data.id} index={index} listName={listName} />),
        )}
      </ul>
    </Fragment>
  );
};

export default DatasetTiles;
