require("jquery");
require("expose-loader?exposes=$!jquery");
require("expose-loader?exposes=jQuery!jquery");

require("corejs-typeahead");
var Bloodhound = require("expose-loader?exposes=Bloodhound!corejs-typeahead/dist/bloodhound.min.js");

require("angular");
require("expose-loader?exposes=angular!angular");
require("angular-resource");

require("angular-typeahead");

require("bootstrap");
require("bootstrap/dist/css/bootstrap.css");

require("font-awesome/css/font-awesome.css");

require("./index.css");
