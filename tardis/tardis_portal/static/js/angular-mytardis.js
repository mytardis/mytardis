var app = angular.module(
    'MyTardis',
    ['ngDialog', 'ngResource', 'multipleSelect', 'ngTagsInput',
     'ngMaterial', 'md.data.table']);

app.config(function($httpProvider) {
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
});
