/* Functions used by Add or Edit Dataset form */

/*
 * Disable Save button immediately after submitting form to prevent
 * duplicate submissions.
 */
export function disableDuplicateSubmit() {
    $("#add-or-edit-dataset-form").submit(function() {
        $(this).find(":submit").prop("disabled", true);
    });
}

$(document).ready(function() {
    disableDuplicateSubmit();
});
