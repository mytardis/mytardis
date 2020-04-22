import React from 'react';
import ReactDOM from 'react-dom';
import DatasetTilesLists from "./components/DatasetTilesLists";

const content = document.getElementById('datasets-pane');
const experimentId = document.getElementById('experiment-id').value;
const shareContainer = document.getElementById('experiment-tab-transfer-datasets');


ReactDOM.render(
  <DatasetTilesLists shareContainer={shareContainer} experimentId={experimentId} />, content,
);
