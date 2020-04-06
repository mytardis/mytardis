import React, { Fragment, useEffect, useState } from 'react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import DatasetTile from './DatasetTile';
import fetchDatasetsForExperiment from './utils/FetchData';


const DatasetTiles = ({ experimentID }) => {
  const [data, setData] = useState([]);
  useEffect(() => {
    fetchDatasetsForExperiment(experimentID).then(result => setData(result));
  }, [experimentID]);
  const onDragEnd = (result) => {
    console.log(result);
  };
  return (
    <DragDropContext onDragEnd={onDragEnd}>
      <Droppable droppableId="list">
        {provided => (
          <div ref={provided.innerRef} {...provided.droppableProps}>
            <Fragment>
              <ul className="datasets thumbnails">
                {data.map(
                  (dataset, index) => (
                    <DatasetTile data={dataset} key={dataset.id} index={index} />),
                )}
              </ul>
            </Fragment>
            {provided.placeholder}
          </div>
        )}
      </Droppable>
    </DragDropContext>
  );
};

export default DatasetTiles;
