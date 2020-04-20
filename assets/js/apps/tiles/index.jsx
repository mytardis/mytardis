import React, {Fragment, useEffect, useState} from "react";
import ReactDOM from 'react-dom';

import { DragDropContext, Droppable } from 'react-beautiful-dnd';
import DatasetTiles from './components/DatasetTiles';
import { fetchDatasetsForExperiment, shareDataset } from "./components/utils/FetchData";

const content = document.getElementById('datasets-pane');
const experimentId = document.getElementById('experiment-id').value;
const shareContainer = document.getElementById('experiment-tab-transfer-datasets');

const DatasetTilesLists = ({ shareContainer }) => {
  const [mainListData, setMainListData] = useState([]);
  const [shareListData, setShareListData] = useState([]);
  const onDragEnd = (result) => {
    // dropped nowhere
    if (!result.destination) {
      return;
    }
    // droppped in same list
    if (result.destination.droppableId === result.source.droppableId) {
      return;
    }
    // dropped from share to main list
    if (result.destination.droppableId === 'main-list'
    && result.source.droppableId === 'share-list') {
      // get body data
      const data = shareListData[result.source.index];
      // update experiment dataset
      shareDataset(JSON.stringify(data), experimentId, result.draggableId)
        .then(() => {
          // fetch data and update main list
          fetchDatasetsForExperiment(experimentId)
            .then(listData => setMainListData(listData));
        });
    }
    // dropped from main to share list
    if (result.destination.droppableId === 'share-list'
    && result.source.droppableId === 'main-list') {
      // get body data
      const data = mainListData[result.source.index];
      // update experiment dataset
      shareDataset(JSON.stringify(data), experimentId, result.draggableId)
        .then(() => {
          // fetch data and update main list
          fetchDatasetsForExperiment(experimentId)
            .then(listData => setMainListData(listData));
        });
    }
  };
  useEffect(() => {
    fetchDatasetsForExperiment(experimentId).then(result => setMainListData(result));
    fetchDatasetsForExperiment(10390).then(result => setShareListData(result));
  }, [experimentId]);
  return (
    <DragDropContext onDragEnd={onDragEnd}>
      <Droppable droppableId="main-list">
        {provided => (
          <div ref={provided.innerRef} {...provided.droppableProps}>
            <DatasetTiles data={mainListData} />
            {provided.placeholder}
          </div>
        )}
      </Droppable>
      {ReactDOM.createPortal(
        <Droppable droppableId="share-list">
          {provided => (
            <div ref={provided.innerRef} {...provided.droppableProps}>
              <DatasetTiles data={shareListData} />
              {provided.placeholder}
            </div>
          )}
        </Droppable>, shareContainer,
      )}
    </DragDropContext>
  );
};

ReactDOM.render(<DatasetTilesLists shareContainer={shareContainer} />, content);
