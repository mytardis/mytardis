import React from 'react';
import ReactDOM from 'react-dom';

import DatasetTiles from './components/DatasetTiles';

const content = document.getElementById('tree_view');
const { href } = window.location;
const experimentId = href.substring(href.lastIndexOf('/') + 1);
ReactDOM.render(<DatasetTiles experimentID={experimentId} />, content);
