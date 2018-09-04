/* tardis/tardis_portal/static/js/jquery/tardis_portal/index.js */

/* global attachExpAccordionClickHandlers, expandFirstExperiments, loadRecentDatasetsSummary */

$(document).ready(function() {
    $(".explink").on("click", function(e) {
        e.stopPropagation();
    });
    $(".dllink").on("click", function(e) {
        e.stopPropagation();
    });

    // var attachExpAccordionClickHandlers = function(accordionToggleClass, accordionToggleIdPrefix, accordionBodyIdPrefix, divIdPrefix, loadDatasetsSummary)
    attachExpAccordionClickHandlers("private-experiment", "private-toggle-", "collapse-", "private-recent-datasets-", loadRecentDatasetsSummary);
    attachExpAccordionClickHandlers("public-experiment", "public-toggle-", "collapsepub-", "public-recent-datasets-", loadRecentDatasetsSummary);
    expandFirstExperiments();
});
