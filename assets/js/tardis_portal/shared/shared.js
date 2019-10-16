import {attachExpAccordionClickHandlers, loadLatestDatasetSummary, expandFirstExperiments} from "../experiment-accordion";

$(document).ready(function() {
    // Load shared exps on page load
    var loadingHTML = "<img src=\"/static/images/ajax-loader.gif\"/><br />";
    $("#myshared").html(loadingHTML);
    $("#myshared").load(
        "/ajax/shared_exps_list/",
        function() {
            attachExpAccordionClickHandlers("accordion-toggle", "toggle-", "collapse-", "latest-dataset-", loadLatestDatasetSummary);
            expandFirstExperiments();

            $(".explink").on("click", function(evt) {
                evt.stopPropagation();
            });
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

                $(".explink").on("click", function(evt) {
                    evt.stopPropagation();
                });
                $(".dllink").on("click", function(evt) {
                    evt.stopPropagation();
                });
            });
    });

    // var attachExpAccordionClickHandlers = function(accordionToggleClass, accordionToggleIdPrefix, accordionBodyIdPrefix, divIdPrefix, loadDatasetsSummary)
    attachExpAccordionClickHandlers("accordion-toggle", "toggle-", "collapse-", "latest-dataset-", loadLatestDatasetSummary);
    expandFirstExperiments();
});

$(document).on("click", ".pagelink", function() {
    var loadingHTML = "<img src=\"/static/images/ajax-loader.gif\"/><br />";
    var href = $(this).attr("href");
    $(this).html(loadingHTML);
    $("#myshared").load(href, function() {
        attachExpAccordionClickHandlers("accordion-toggle", "toggle-", "collapse-", "latest-dataset-", loadLatestDatasetSummary);
        expandFirstExperiments();
    });
    return false;
});

