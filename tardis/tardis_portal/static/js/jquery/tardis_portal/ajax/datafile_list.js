/* tardis/tardis_portal/static/js/jquery/tardis_portal/ajax/datafile_list.js */
 
/* global showMsg */

$(function() {
    $(".archived-file").tooltip({
        "title":
        "This file is archived. " +
        "Press the Recall button to request a download link via email."
    });

    $(".recall-datafile").on("click", function(evt) {
        var recallUrl = $(this).data("recall-url");
        var recallButton = $(this);
        $.get(recallUrl)
            .done(function() {
                // Don't add disabled attribute, because that disables tooltips
                // Instead, add disabled CSS class and remove click handler
                recallButton.addClass("disabled");
                recallButton.off("click");
                recallButton.html(
                    "<i class=\"fa fa-spinner fa-spin fa-lg\"></i>");
                recallButton.attr(
                    "title",
                    "An email will be sent when the recall is complete");
                recallButton.tooltip();
            })
            .fail(function(data) {
                // Don't add disabled attribute, because that disables tooltips
                // Instead, add disabled CSS class and remove click handler
                recallButton.addClass("disabled");
                recallButton.off("click");
                recallButton.attr("title", "Recall request failed");
                recallButton.tooltip();
            });
    });
}());
