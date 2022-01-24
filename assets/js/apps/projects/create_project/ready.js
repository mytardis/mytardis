/* Functions used by Create Experiment form */

/*
 * Disable Save button immediately after submitting form to prevent
 * duplicate submissions.
 */
export function disableDuplicateSubmit() {
    $("#create_experiment_form").submit(function() {
        $(this).find(":submit").prop("disabled", true);
    });
}

$(document).ready(function() {
    disableDuplicateSubmit();
});
