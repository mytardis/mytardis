import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import DatasetTile from './DatasetTile';

const DatasetTiles = ({ data, listName, onDownloadSelect }) => {
  const onCheckboxSelected = (id, event) => {
    onDownloadSelect(id, event);
  };
  return (
    <Fragment>
      {listName === 'share-list'
        ? (
          <ul className="datasets thumbnails">
            {data.map(
              (dataset, index) => (
                <DatasetTile
                  data={dataset}
                  key={data.id}
                  index={index}
                  listName={listName}
                  showDownloadCheckbox={false}
                />
              ),
            )}
          </ul>
        )
        : (
          <ul className="datasets thumbnails">
            {data.map(
              (dataset, index) => (
                <DatasetTile
                  data={dataset}
                  key={data.id}
                  index={index}
                  listName={listName}
                  onDownloadSelect={onCheckboxSelected}
                  showDownloadCheckbox
                />
              ),
            )}
          </ul>
        )


      }

    </Fragment>
  );
};
DatasetTiles.defaultProps = {
  onDownloadSelect: () => {},
};
DatasetTiles.propTypes = {
  data: PropTypes.array.isRequired,
  listName: PropTypes.string.isRequired,
  onDownloadSelect: PropTypes.func,
};
export default DatasetTiles;
