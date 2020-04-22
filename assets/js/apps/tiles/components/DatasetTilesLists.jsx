import React, { useEffect, useState } from 'react';
import ReactDOM from 'react-dom';
import { DragDropContext, Droppable } from 'react-beautiful-dnd';
import PropTypes from "prop-types";
import { fetchDatasetsForExperiment, fetchExperimentList, shareDataset } from './utils/FetchData';
import DatasetTiles from './DatasetTiles';
import ExperimentListDropDown from './SelectExperiment';

const DatasetTilesLists = ({ shareContainer, experimentId }) => {
  const [mainListData, setMainListData] = useState([]);
  const [shareListData, setShareListData] = useState([]);
  const [expListValue, setExpListValue] = useState();
  const onDragEnd = (result) => {
    // dropped nowhere
    if (!result.destination) {
      return;
    }
    // dropped in the same list
    if (result.destination.droppableId === result.source.droppableId) {
      return;
    }
    // dropped from share to main list
    if (result.destination.droppableId === 'main-list'
    && result.source.droppableId === 'share-list') {
      // get body data
      const data = shareListData[result.source.index];
      // update experiment dataset
      const datasetId = result.draggableId.split('_')[1];
      shareDataset(JSON.stringify(data), experimentId, datasetId)
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
      const datasetId = result.draggableId.split('_')[1];
      shareDataset(JSON.stringify(data), expListValue, datasetId)
        .then(() => {
          // fetch data and update share list
          fetchDatasetsForExperiment(expListValue)
            .then(listData => setShareListData(listData));
        });
    }
  };
  const onChange = (event) => {
    event.preventDefault();
    setExpListValue(event.target.value);
    fetchDatasetsForExperiment(event.target.value).then(result => setShareListData(result));
  };
  useEffect(() => {
    fetchDatasetsForExperiment(experimentId).then(result => setMainListData(result));
    // load initial list
    fetchExperimentList().then((expList) => {
      // TODO
      setExpListValue(expList[0].id);
      fetchDatasetsForExperiment(expList[0].id).then(result => setShareListData(result));
    });
  }, [experimentId]);
  return (
    <DragDropContext onDragEnd={onDragEnd}>
      <Droppable droppableId="main-list">
        {provided => (
          <div ref={provided.innerRef} {...provided.droppableProps}>
            <DatasetTiles data={mainListData} listName="main-list" />
            {provided.placeholder}
          </div>
        )}
      </Droppable>
      {ReactDOM.createPortal(
        <Droppable droppableId="share-list">
          {provided => (
            <div ref={provided.innerRef} {...provided.droppableProps}>
              <ExperimentListDropDown onChange={onChange} value={expListValue} />
              <DatasetTiles data={shareListData} listName="share-list" />
              {provided.placeholder}
            </div>
          )}
        </Droppable>, shareContainer,
      )}
    </DragDropContext>
  );
};
DatasetTilesLists.propTypes = {
  shareContainer: PropTypes.object.isRequired,
  experimentId: PropTypes.string.isRequired,
};
export default DatasetTilesLists;
