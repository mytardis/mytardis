import React from "react";

import ReactDOM from "react-dom";

import TreeView from './components/TreeView';


const content = document.getElementById('tree_view');
const href = window.location.href;
const datasetId = href.substring(href.lastIndexOf("/")+1);
ReactDOM.render(<TreeView datasetId={datasetId}/>, content);
