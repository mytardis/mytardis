/* Functions used by Create Experiment form */

/*
 * Disable Save button immediately after submitting form to prevent
 * duplicate submissions.
 */
export function disableDuplicateSubmit() {
    $("#create_experiment_form").on("submit", function(e) {
        var $form = $(this);
        if ($form.data("submitted") === true) {
            e.preventDefault();
        } else {
            $form.data("submitted", true);
        }
    });
}

$(document).ready(function() {
    disableDuplicateSubmit();
});
