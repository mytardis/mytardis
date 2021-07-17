/* global QUnit */

import { disableDuplicateSubmit } from "../../../assets/js/tardis_portal/create_experiment/ready.js";

QUnit.module("tardis_portal.create_experiment");

QUnit.test("Test disabling duplicate submit in create experiment form", function(assert) {

    $("#qunit-fixture").append(`
      <form id="create_experiment_form">
        <button type="submit">Save</button>
      </form>`);

    // Submit form without applying the disableDuplicateSubmit() function:
    $("#create_experiment_form").submit();
    assert.notOk($("#create_experiment_form").data("submitted"));

    // Submit form after applying the disableDuplicateSubmit() function:
    disableDuplicateSubmit();
    $("#create_experiment_form").submit();
    assert.ok($("#create_experiment_form").data("submitted"));

});
