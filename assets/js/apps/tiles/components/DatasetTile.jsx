import React, { Fragment } from 'react';
import { Draggable } from 'react-beautiful-dnd';
import DatafileCountBadge from '../../badges/components/DatafileCountBadge';
import DatasetSizeBadge from '../../badges/components/DatasetSizeBadge';

// eslint-disable-next-line react/prop-types
const DatasetTile = ({ data, listName, index }) => {
  const experimentData = {
    datafile_count: data.file_count,
  };
  const datasetData = {
    dataset_size: data.size,
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
                    className="dataset_checkbox ml-2"
                    style={{ display: 'inline' }}
                    value={data.id}
                  />
                </label>
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

export default DatasetTile;
