import React from 'react';

import ReactDOM from 'react-dom';

import TreeView from './components/TreeView';

const hsmEnabled = document.getElementById('hsm-enabled').value === 'True';
const content = document.getElementById('tree_view');
const { href } = window.location;
const datasetId = href.substring(href.lastIndexOf('/') + 1);
ReactDOM.render(<TreeView datasetId={datasetId} hsmEnabled={hsmEnabled} />, content);
