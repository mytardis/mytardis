import {
    attachExpAccordionClickHandlers,
    expandFirstExperiments,
    loadRecentDatasetsSummary,
    handleExpAccordionLink
} from "../experiment-accordion";

$(document).ready(function() {
    $("#private-experiments .accordion-body").collapse({parent: "#private-experiments", toggle: false});
    $("#public-experiments .accordion-body").collapse({parent: "#public-experiments", toggle: false});
    $(".explink").on("click", handleExpAccordionLink);
    $(".dllink").on("click", function(e) {
        e.stopPropagation();
    });
    attachExpAccordionClickHandlers("private-experiment", "private-toggle-", "collapse-", "private-recent-datasets-", loadRecentDatasetsSummary);
    attachExpAccordionClickHandlers("public-experiment", "public-toggle-", "collapsepub-", "public-recent-datasets-", loadRecentDatasetsSummary);
    setTimeout(expandFirstExperiments, 100);
});
