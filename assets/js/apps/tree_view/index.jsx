import React from 'react';

import ReactDOM from 'react-dom';

import TreeView from './components/TreeView';

const hsmEnabled = document.getElementById('hsm-enabled').value === 'True';
const content = document.getElementById('tree_view');
const { href } = window.location;
const datasetId = href.substring(href.lastIndexOf("/", href.lastIndexOf("/") - 1 ) + 1, href.lastIndexOf("/"));
ReactDOM.render(<TreeView datasetId={datasetId} hsmEnabled={hsmEnabled} />, content);
