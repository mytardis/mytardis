const angular = require("angular");
require("angular-resource");
/*<script type="text/javascript" src="{% static 'js/lib/angular-animate-1.6.10/angular-animate.min.js' %}"></script>
<script type="text/javascript" src="{% static 'js/lib/angular-aria-1.6.10/angular-aria.min.js' %}"></script>
<script type="text/javascript" src="{% static 'js/lib/angular-messages-1.6.10/angular-messages.min.js' %}"></script>
<script type="text/javascript" src="{% static 'js/lib/angular-material-1.1.10/angular-material.min.js' %}"></script>

<script type="text/javascript" src="{% static 'js/lib/angular-material-data-table-0.10.10/dist/md-data-table.min.js' %}"></script>
<script type="text/javascript" src="{% static 'js/lib/default-passive-events-1.0.10/dist/index.js'%}"></script>
<link type="text/css" href="{% static 'js/lib/angular-material-1.1.10/angular-material.min.css' %}" rel="stylesheet" />
<link type="text/css" href="{% static 'js/lib/angular-material-data-table-0.10.10/dist/md-data-table.min.css' %}" rel="stylesheet" />

<script id="my-publications" type="text/javascript" src="{% static 'my-publications/my_publications.js'%}"></script>
<script type="text/javascript" src="{% static 'publication-actions/publication_actions.js'%}"></script>
<script type="text/javascript" src="{% static 'publication-tokens/publication_tokens.js'%}"></script>
<script type="text/javascript" src="{% static 'publication-form/publication_form.js'%}"></script>
<link type="text/css" href="{% static 'my-publications/my_publications.css'%}" rel="stylesheet"/>
<link type="text/css" href="{% static 'publication-form/publication_form.css' %}" rel="stylesheet" />*/
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