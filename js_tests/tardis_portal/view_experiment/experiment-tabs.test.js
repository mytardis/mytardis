/* global QUnit, _ */

import {populateExperimentTabs} from "../../../assets/js/tardis_portal/view_experiment/experiment-tabs";

QUnit.module("tardis_portal.view_experiment.experiment-tabs", {
    beforeEach: function(assert) {
        $.ajaxSetup({async: false});
    },
    afterEach: function(assert) {
        $.ajaxSetup({async: true});
    }
});
QUnit.test("Load experiment tabs", function(assert) {

    $("#qunit-fixture").append(`
        <ul id="experiment-tabs" class="nav nav-pills">
          <li><a data-bs-toggle="tab" title="Description" data-url="/ajax/experiment/1/description">Description</a></li>
          <li><a data-bs-toggle="tab" title="Metadata" data-url="/ajax/experiment_metadata/1/">Metadata</a></li>
          <li><a data-bs-toggle="tab" title="Sharing" data-url="/ajax/experiment/1/share">Sharing</a></li>
          <li><a data-bs-toggle="tab" title="Transfer Datasets" data-url="/ajax/experiment/1/dataset-transfer">Transfer Datasets</a></li>
        </ul>
        <div class="tab-content">
          <div id="experiment-tab-description">
            <div id="experiment_description" class="dl-horizontal">
              <!-- ... -->
            </div>
          </div>
        </div>`);

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

    populateExperimentTabs();
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
