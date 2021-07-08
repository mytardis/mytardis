import React from 'react';

import ReactDOM from 'react-dom';

import PublicationsHome from "../components/PublicationsHome";

// react stuff

const content = document.getElementById('publication-workflow-app');
console.log(content);
ReactDOM.render(<PublicationsHome />, content);

/*
const angular = require("angular");

require("angular-resource");

require('./js/lib/ng-dialog/js/ngDialog.min');
require('./js/lib/ng-dialog/css/ngDialog.min.css');
require('./js/lib/ng-dialog/css/ngDialog-theme-default.min.css');

require('./js/lib/angular-aria-1.6.10/angular-aria.min');
require('./js/lib/angular-animate-1.6.10/angular-animate.min');
require('./js/lib/angular-messages-1.6.10/angular-messages.min');
require('./js/lib/angular-material-1.1.10/angular-material.min');

require('./js/lib/angular-material-data-table-0.10.10/dist/md-data-table.min');
require('./js/lib/default-passive-events-1.0.10/dist/index');
require('./js/lib/angular-material-1.1.10/angular-material.min.css');
require('./js/lib/angular-material-data-table-0.10.10/dist/md-data-table.min.css');


require('./my-publications/my_publications.css');
require('./publication-form/publication_form.css');


var app = angular.module('publicationWorkflow', ["ngMaterial", "ngAria", "ngResource", 'ngDialog', 'md.data.table']);
app.config(function($httpProvider) {
    $httpProvider.defaults.xsrfCookieName = "csrftoken";
    $httpProvider.defaults.xsrfHeaderName = "X-CSRFToken";
});
var myPublications = document.getElementById("my-publications");
require('./my-publications/my_publications');
require('./publication-actions/publication_actions');
require('./publication-tokens/publication_tokens');
require('./publication-form/publication_form');

*/
