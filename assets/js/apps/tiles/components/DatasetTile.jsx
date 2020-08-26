import React from 'react';
import { Draggable } from 'react-beautiful-dnd';
import PropTypes from 'prop-types';
import DatafileCountBadge from '../../badges/components/DatafileCountBadge';
import DatasetSizeBadge from '../../badges/components/DatasetSizeBadge';

const DatasetTile = ({
  data, listName, index, onDownloadSelect, showDownloadCheckbox,
}) => {
  const experimentData = {
    datafile_count: data.file_count,
  };
  const datasetData = {
    dataset_size: data.size,
  };
  const onCheckBoxSelect = (id, event) => {
    onDownloadSelect(id, event);
  };
  return (
    <Draggable draggableId={`${listName}_${data.id.toString()}`} index={index}>
      {provided => (
        <div
          ref={provided.innerRef}
          {...provided.draggableProps}
          {...provided.dragHandleProps}
        >
          <li className="dataset card mb-2">
            <div className="card-body">
              <div className="float-left" style={{ marginRight: '10px' }}>
                <div style={{ display: 'flex', textAlign: 'center', fontSize: '32px' }}>
                  <i className="fa fa-folder-open o-6" />
                </div>
                <br />
                {showDownloadCheckbox
                  ? (
                    <label
                      className="label label-info"
                      htmlFor={`dataset-checkbox-${data.id}`}
                      title="Mark dataset for download"
                    >
                      <i className="fa fa-download" />
                      <input
                        id={`dataset-checkbox-${data.id}`}
                        name="dataset"
                        type="checkbox"
                        onChange={e => onCheckBoxSelect(data.id, e)}
                        className="dataset_checkbox ml-2"
                        style={{ display: 'inline' }}
                        value={data.id}
                      />
                    </label>
                  ) : ''}
              </div>
              <div className="float-left" style={{ marginRight: '10px' }} />
              <div className="float-right" style={{ textAlign: 'right' }}>
                <p>
                  <DatafileCountBadge experimentData={experimentData} />
                </p>
                <p>
                  <DatasetSizeBadge datasetData={datasetData} />
                </p>
              </div>
              <div className="float-left ds-thumb" style={{ marginRight: '10px' }}>
                <canvas style={{ width: '100px' }} />
              </div>
              <div className="float-left">
                <p className="mb-2">
                  <a className="dataset-link" href={data.url}>
                    {data.description}
                  </a>
                </p>
                {data.show_instr_facil ? (
                  <p style={{ color: 'grey', fontSize: '100%' }}>
                    {data.instrument ? `Instrument: ${data.instrument}`
                      : '' }
                    <br />
                    {data.facility ? (
                      `Facility: ${data.facility}`
                    ) : ''}
                  </p>
                ) : ''}
                <div style={{ clear: 'both' }} />
              </div>
            </div>
          </li>
        </div>
      )}

    </Draggable>

  );
};
DatasetTile.defaultProps = {
  showDownloadCheckbox: () => {},
};
DatasetTile.propTypes = {
  data: PropTypes.object.isRequired,
  listName: PropTypes.string.isRequired,
  index: PropTypes.number.isRequired,
  onDownloadSelect: PropTypes.func.isRequired,
  showDownloadCheckbox: PropTypes.bool,
};

export default DatasetTile;
