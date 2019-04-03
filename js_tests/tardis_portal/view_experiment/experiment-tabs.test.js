/* eslint global-strict: 0, strict: 0, no-console: 0, object-shorthand: 0,
          no-unused-vars: [2, {"vars": "local", "args": "none"}] */
/* global QUnit, _, experimentabs */
"use strict";
require("experimentabs");
require("bootstrap");
require("mustache");

QUnit.module("tardis_portal.view_experiment.experiment-tabs", {
    beforeEach: function(assert) {
        $.ajaxSetup({async: false});
    },
    afterEach: function(assert) {
        $.ajaxSetup({async: true});
    }
});
QUnit.test("Load experiment tabs", function(assert) {

    $("#qunit-fixture").append(
        "<ul id=\"experiment-tabs\" class=\"nav nav-pills\">\n" +
        "  <li><a data-toggle=\"tab\" title=\"Description\" href=\"/ajax/experiment/1/description\">Description</a></li>\n" +
        "  <li><a data-toggle=\"tab\" title=\"Metadata\" href=\"/ajax/experiment_metadata/1/\">Metadata</a></li>\n" +
        "  <li><a data-toggle=\"tab\" title=\"Sharing\" href=\"/ajax/experiment/1/share\">Sharing</a></li>\n" +
        "  <li><a data-toggle=\"tab\" title=\"Transfer Datasets\" href=\"/ajax/experiment/1/dataset-transfer\">Transfer Datasets</a></li>\n" +
        "</ul>\n" +
        "<div class=\"tab-content\">\n" +
        "  <div id=\"experiment-tab-description\">\n" +
        "    <div id=\"experiment_description\" class=\"dl-horizontal\">\n" +
        "      <!-- ... -->\n" +
        "    </div>\n" +
        "  </div>\n" +
        "</div>\n"
    );

    $.mockjax({
        url: "/ajax/experiment_metadata/1/",
        contentType: "text/html",
        responseText: "Experiment metadata pane mock content"
    });

    $.mockjax({
        url: "/ajax/experiment/1/share",
        contentType: "text/html",
        responseText: "Experiment sharing pane mock content"
    });

    $.mockjax({
        url: "/ajax/experiment/1/dataset-transfer",
        contentType: "text/html",
        responseText: "Experiment dataset transfer pane mock content"
    });

    // Check that underscore library is loaded
    // as it is required to load view_experiment/experiment-tabs.js:
    assert.ok(_.isEmpty({}));

    // Ensure that the tab panes which haven't been loaded yet are not in the fixture:
    var expMetadataDiv = $("#qunit-fixture").find("#experiment-tab-metadata");
    assert.equal(expMetadataDiv.length, 0);

    var expSharingDiv = $("#qunit-fixture").find("#experiment-tab-sharing");
    assert.equal(expSharingDiv.length, 0);

    var expDatasetTransferDiv = $("#qunit-fixture").find("#experiment-tab-transfer-datasets");
    assert.equal(expDatasetTransferDiv.length, 0);

    experimentabs.populateExperimentTabs();
    // Ensure that experiment metadata tab pane's content has been loaded:
    expMetadataDiv = $("#qunit-fixture").find("#experiment-tab-metadata");
    assert.equal(expMetadataDiv.html(), "Experiment metadata pane mock content");

    // Ensure that experiment sharing tab pane's content has been loaded:
    expSharingDiv = $("#qunit-fixture").find("#experiment-tab-sharing");
    assert.equal(expSharingDiv.html(), "Experiment sharing pane mock content");

    // Ensure that experiment dataset transfer tab pane's content has been loaded:
    expDatasetTransferDiv = $("#qunit-fixture").find("#experiment-tab-transfer-datasets");
    assert.equal(expDatasetTransferDiv.html(), "Experiment dataset transfer pane mock content");
});
