import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import DatasetTile from './DatasetTile';

const DatasetTiles = ({ data, listName }) => (
  <Fragment>
    <ul className="datasets thumbnails">
      {data.map(
        (dataset, index) => (
          <DatasetTile data={dataset} key={data.id} index={index} listName={listName} />),
      )}
    </ul>
  </Fragment>
);
DatasetTiles.propTypes = {
  data: PropTypes.object.isRequired,
  listName: PropTypes.string.isRequired,
};
export default DatasetTiles;
