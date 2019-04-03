"use strict";

const angular = require("angular");
require("expose-loader?angular!angular");
require("ng-dialog");
require("angular-resource");

var app = angular.module("facilityOverview", ["ngDialog", "ngResource"]);

app.config(function($httpProvider) {
    $httpProvider.defaults.xsrfCookieName = "csrftoken";
    $httpProvider.defaults.xsrfHeaderName = "X-CSRFToken";
});
require("./facility_view");
