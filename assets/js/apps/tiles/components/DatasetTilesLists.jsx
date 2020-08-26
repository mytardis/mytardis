import React, { Fragment, useEffect, useState } from 'react';
import ReactDOM from 'react-dom';
import { DragDropContext, Droppable } from 'react-beautiful-dnd';
import PropTypes from 'prop-types';
import { css } from '@emotion/core';
import Cookies from 'js-cookie';
import {
  fetchDatasetsForExperiment,
  fetchExperimentList,
  fetchExperimentPermissions,
  shareDataset,
} from './utils/FetchData';
import DatasetTiles from './DatasetTiles';
import ExperimentListDropDown from './SelectExperiment';
import DatasetPaneTopPanel from './DatasetPaneTopPanel';
import Spinner from '../../badges/components/utils/Spinner';

const DatasetTilesLists = ({ shareContainer, experimentId }) => {
  const [mainListData, setMainListData] = useState([]);
  const [shareListData, setShareListData] = useState([]);
  const [expListData, setExpListData] = useState();
  const [expListValue, setExpListValue] = useState();
  const [selectedDatasetIds, setSelectedDatasetIds] = useState([]);
  const [experimentPermissions, setExperimentPermissions] = useState({});
  const [mainListDataLoading, setMainListDataLoading] = useState(true);
  const csrfToken = Cookies.get('csrftoken');
  const spinnerCss = css`
    float: right;
  `;
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
  const onDownloadSelect = (id, event) => {
    if (event.target.checked) {
      setSelectedDatasetIds([id].concat(selectedDatasetIds));
    } else {
      setSelectedDatasetIds(selectedDatasetIds.filter(item => item !== id));
    }
  };
  const onChange = (event) => {
    event.preventDefault();
    setExpListValue(event.target.value);
    fetchDatasetsForExperiment(event.target.value).then(result => setShareListData(result));
  };
  useEffect(() => {
    fetchDatasetsForExperiment(experimentId).then(result => setMainListData(result))
      .then(() => setMainListDataLoading(false));
    // load initial list
    fetchExperimentList().then((expList) => {
      // TODO
      setExpListData(expList);
      fetchDatasetsForExperiment(expList[0].id).then(result => setShareListData(result));
    });
    // load permissions
    fetchExperimentPermissions(experimentId).then(result => setExperimentPermissions(result));
  }, [experimentId]);
  return (
    <Fragment>
      {mainListDataLoading
        ? <Spinner override={spinnerCss} />
        : (
          <Fragment>
            <DatasetPaneTopPanel
              count={mainListData.length}
              experimentID={experimentId}
              selectedDatasets={selectedDatasetIds}
              csrfToken={csrfToken}
              experimentPermissions={experimentPermissions}
            />
            <DragDropContext onDragEnd={onDragEnd}>
              <Droppable droppableId="main-list">
                {provided => (
                  <div ref={provided.innerRef} {...provided.droppableProps}>
                    <DatasetTiles data={mainListData} listName="main-list" onDownloadSelect={onDownloadSelect} />
                    {provided.placeholder}
                  </div>
                )}
              </Droppable>
              {ReactDOM.createPortal(
                <Droppable droppableId="share-list">
                  {provided => (
                    <div ref={provided.innerRef} {...provided.droppableProps}>
                      {expListData
                        ? (
                          <ExperimentListDropDown
                            onChange={onChange}
                            experimentListData={expListData}
                          />
                        ) : <span />
              }
                      <DatasetTiles data={shareListData} listName="share-list" />
                      {provided.placeholder}
                    </div>
                  )}
                </Droppable>, shareContainer,
              )}
            </DragDropContext>
          </Fragment>
        )
        }
    </Fragment>
  );
};
DatasetTilesLists.propTypes = {
  shareContainer: PropTypes.object.isRequired,
  experimentId: PropTypes.string.isRequired,
};
export default DatasetTilesLists;
