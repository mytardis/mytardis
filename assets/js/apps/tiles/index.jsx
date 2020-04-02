import React from 'react';
import ReactDOM from 'react-dom';

import DatasetTiles from './components/DatasetTiles';

const content = document.getElementById('datasets-pane');
const experimentId = document.getElementById('experiment-id').value;
ReactDOM.render(<DatasetTiles experimentID={experimentId} />, content);
