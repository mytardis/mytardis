const angular = require("angular");
require("expose-loader?exposes=angular!angular");
require("angular-resource");

var app = angular.module("facilityOverview", ["ngResource"]);

app.config(function($httpProvider) {
    $httpProvider.defaults.xsrfCookieName = "csrftoken";
    $httpProvider.defaults.xsrfHeaderName = "X-CSRFToken";
});
require("./facility_view");
