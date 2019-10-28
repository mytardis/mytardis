/* global QUnit */
  
import { disableDuplicateSubmit } from "../../../assets/js/tardis_portal/add_or_edit_dataset/ready.js";

QUnit.module("tardis_portal.add_or_edit_dataset");

QUnit.test("Test disabling duplicate submit in add or edit dataset form", function(assert) {

    $("#qunit-fixture").append(`
      <form id="add-or-edit-dataset-form">
        <button type="submit">Save</button>
      </form>`);

    // Submit form without applying the disableDuplicateSubmit() function:
    $("#add-or-edit-dataset-form").submit();
    assert.notOk($("#add-or-edit-dataset-form").find(":submit").prop("disabled"));

    // Submit form after applying the disableDuplicateSubmit() function:
    disableDuplicateSubmit();
    $("#add-or-edit-dataset-form").submit();
    assert.ok($("#add-or-edit-dataset-form").find(":submit").prop("disabled"));

});
