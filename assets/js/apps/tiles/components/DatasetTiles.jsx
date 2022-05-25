import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import DatasetTile from './DatasetTile';

const DatasetTiles = ({
  data, listName, onDownloadSelect, hsmEnabled,
}) => {
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
                  key={index}
                  index={index}
                  listName={listName}
                  showDownloadCheckbox={false}
                  hsmEnabled={hsmEnabled}
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
                  key={index}
                  index={index}
                  listName={listName}
                  onDownloadSelect={onCheckboxSelected}
                  showDownloadCheckbox
                  hsmEnabled={hsmEnabled}
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
  hsmEnabled: PropTypes.bool.isRequired,
};
export default DatasetTiles;
