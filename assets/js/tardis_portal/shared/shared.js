import {
    attachExpAccordionClickHandlers,
    loadLatestDatasetSummary,
    expandFirstExperiments,
    handleExpAccordionLink
} from "../experiment-accordion";

$(document).ready(function() {
    // Load shared exps on page load
    var loadingHTML = "<img src=\"/static/images/ajax-loader.gif\"/><br />";
    $("#myshared").html(loadingHTML);
    $("#myshared").load(
        "/ajax/shared_exps_list/",
        function() {
            attachExpAccordionClickHandlers("accordion-toggle", "toggle-", "collapse-", "latest-dataset-", loadLatestDatasetSummary);
            expandFirstExperiments();
            $(".explink").on("click", handleExpAccordionLink);
            $(".dllink").on("click", function(evt) {
                evt.stopPropagation();
            });
        });

    // Create a reload event handler
    $("#myshared").on("reload", function() {
        $(this).html(loadingHTML);
        $(this).load(
            "/ajax/shared_exps_list/",
            function() {
                attachExpAccordionClickHandlers("accordion-toggle", "toggle-", "collapse-", "latest-dataset-", loadLatestDatasetSummary);
                expandFirstExperiments();
                $(".explink").on("click", handleExpAccordionLink);
                $(".dllink").on("click", function(evt) {
                    evt.stopPropagation();
                });
            });
    });
    attachExpAccordionClickHandlers("accordion-toggle", "toggle-", "collapse-", "latest-dataset-", loadLatestDatasetSummary);
    expandFirstExperiments();
});

$(document).on("click", ".page-link", function() {
    var loadingHTML = "<img src=\"/static/images/ajax-loader.gif\"/><br />";
    var href = $(this).attr("href");
    $(this).html(loadingHTML);
    $("#myshared").load(href, function() {
        attachExpAccordionClickHandlers("accordion-toggle", "toggle-", "collapse-", "latest-dataset-", loadLatestDatasetSummary);
        expandFirstExperiments();
    });
    return false;
});

