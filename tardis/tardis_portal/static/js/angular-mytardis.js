var app = angular.module(
    'MyTardis',
    ['ngDialog', 'ngResource', 'multipleSelect','ngTagsInput']);

app.config(function($httpProvider) {
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
});
