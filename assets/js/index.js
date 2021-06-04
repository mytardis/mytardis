"use strict";

require("jquery");
require("expose-loader?exposes=$!jquery");
require("expose-loader?exposes=jQuery!jquery");
require("jquery-ui-dist/jquery-ui.min");
require("bootstrap");
require("bootstrap-3-typeahead");
require("underscore/underscore-min");
require("expose-loader?exposes=_!underscore/underscore-min");
require("underscore.string/dist/underscore.string");
require("expose-loader?exposes=s!underscore.string/dist/underscore.string");
require("sprintf-js/dist/sprintf.min");
require("expose-loader?exposes=sprintf!sprintf-js/dist/sprintf.min");
require("clipboard");
require("expose-loader?exposes=ClipboardJS!clipboard/dist/clipboard");
require('he');
require('expose-loader?exposes=he!he/he');
//css
require("bootstrap/dist/css/bootstrap.css");
require("../css/jquery-ui/jquery-ui-1.8.18.custom.css");
require("font-awesome/css/font-awesome.css");
require("../css/default.css");
require("../css/facility-overview.css");
require("blueimp-file-upload/css/jquery.fileupload.css");
