import React from 'react';
import ReactDOM from 'react-dom';
import DatasetTilesLists from './components/DatasetTilesLists';

const content = document.getElementById('datasets-pane');
const experimentId = document.getElementById('experiment-id').value;
const shareContainer = document.getElementById('experiment-tab-transfer-datasets');
const hsmEnabled = document.getElementById('hsm-enabled').value === 'True';

ReactDOM.render(
  <DatasetTilesLists
    shareContainer={shareContainer}
    experimentId={experimentId}
    hsmEnabled={hsmEnabled}
  />, content,
);
