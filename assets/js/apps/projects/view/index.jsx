import React, { Suspense, Fragment } from "react";
import ReactDOM from "react-dom";
import "./index.css";
import ProjectPage from "./components/ProjectPage/ProjectPage";
import * as serviceWorker from "./serviceWorker";


let mountPoint = document.getElementById('project-app');

const { href } = window.location;
// console.log(href);

const projectId = href.substring(href.lastIndexOf("/", href.lastIndexOf("/") - 1 ) + 1, href.lastIndexOf("/"));

ReactDOM.render(
  <div>
  <ProjectPage projectId={projectId} />
  </div>,
  mountPoint
);

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://bit.ly/CRA-PWA
serviceWorker.unregister();
