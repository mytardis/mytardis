/* global QUnit */
/* eslint global-strict: 0, strict: 0 */
'use strict';

// Tests for tardis/tardis_portal/static/js/main.js

QUnit.module("tardis_portal.main", {
    beforeEach: function(assert) {
        $.ajaxSetup({ async: false });
    },
    afterEach: function(assert) {
        $.ajaxSetup({ async: true });
    }
});

QUnit.test("Test activating search autocomplete", function(assert) {

    $.getScript("../tardis/tardis_portal/static/js/main.js", function(data, textStatus, jqxhr) {
        assert.equal(jqxhr.status, 200);
        console.log("Loaded main.js");
    });

    //url: "/search/parameter_field_list/?authMethod=localdb",
    $.mockjax({
        url: "/search/parameter_field_list/",
        contentType: "text/plain",
        responseText:
            "Test User1:username+Test User2:username+" +
            "dataset_id_stored:search_field+" +
            "experiment_id_stored:search_field+" +
            "datafile_filename:search_field"
    });

    activateSearchAutocomplete();
});
