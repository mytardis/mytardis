/* global QUnit */
/* eslint global-strict: 0, strict: 0, no-console: 0, no-unused-vars: [2, {"vars": "local", "args": "none"}] */
"use strict";

// Tests for tardis/tardis_portal/static/js/main.js

QUnit.module("tardis_portal.main", {
    beforeEach: function(assert) {
        $.ajaxSetup({ async: false });
    },
    afterEach: function(assert) {
        $.ajaxSetup({ async: true });
    }
});

QUnit.test("Test loading main.js", function(assert) {

    $.getScript("../tardis/tardis_portal/static/js/main.js", function(data, textStatus, jqxhr) {
        assert.equal(jqxhr.status, 200);
        console.log("Loaded main.js");
    });
});
