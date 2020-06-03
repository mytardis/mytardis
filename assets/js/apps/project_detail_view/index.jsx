import React, { Suspense, Fragment } from "react";
import ReactDOM from "react-dom";
import "./index.css";
import Project from "./components/Project/Project";
import * as serviceWorker from "./serviceWorker";


let mountPoint = document.getElementById('project-app');

const { href } = window.location;
console.log(href);

const projectId = href.substring(href.lastIndexOf("/") + 1);
console.log(projectId);

// fetch the project?
async function fetchProject(id) {
  let response = await fetch(
    `http://130.216.218.45:80/api/v1/project/?id=${projectId}`
  );
  let data = await response.json();
  return data;
}

ReactDOM.render(
  <div>
  <Project projectId={projectId} />,
  </div>,
  mountPoint
);

// future render menthod using suspense
// ReactDOM.render(
//   <React.StrictMode>
//     {/* <App /> */}
//     <Suspense fallback={<div>Loading...</div>}>
//       {/* <Project projectId={projectId} /> */}
//       <Project projectId={fetchProject(projectId)} />
//     </Suspense>
//   </React.StrictMode>,
//   mountPoint
// );

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://bit.ly/CRA-PWA
serviceWorker.unregister();
