var angular = require("angular");
require("angular-resource");

var app = angular.module("facilityOverview", ["ngResource"]);

app.config(function($httpProvider) {
    $httpProvider.defaults.xsrfCookieName = "csrftoken";
    $httpProvider.defaults.xsrfHeaderName = "X-CSRFToken";
});
require("./facility_view");
