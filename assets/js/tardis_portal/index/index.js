import {attachExpAccordionClickHandlers, expandFirstExperiments, loadRecentDatasetsSummary} from "../experiment-accordion";
import {attachProjAccordionClickHandlers, expandFirstProjects, loadRecentExperimentsSummary} from "../../apps/projects/project-accordion";

$(document).ready(function() {
    $("#private-experiments .accordion-body").collapse({parent: "#private-experiments", toggle: false});
    $("#public-experiments .accordion-body").collapse({parent: "#public-experiments", toggle: false});
    $(".explink").on("click", function(e) {
        e.stopPropagation();
    });
    $(".dllink").on("click", function(e) {
        e.stopPropagation();
    });
    $(".projlink").on("click", function(e) {
        e.stopPropagation();
    });
    // var attachExpAccordionClickHandlers = function(accordionToggleClass, accordionToggleIdPrefix, accordionBodyIdPrefix, divIdPrefix, loadDatasetsSummary)
    attachExpAccordionClickHandlers("private-experiment", "private-toggle-", "collapse-", "private-recent-datasets-", loadRecentDatasetsSummary);
    attachExpAccordionClickHandlers("public-experiment", "public-toggle-", "collapsepub-", "public-recent-datasets-", loadRecentDatasetsSummary);
    expandFirstExperiments();
    // var attachProjAccordionClickHandlers = function(accordionToggleClass, accordionToggleIdPrefix, accordionBodyIdPrefix, divIdPrefix, loadExperimentsSummary)
    attachProjAccordionClickHandlers("private-project", "private-toggle-", "collapse-", "private-recent-experiments-", loadRecentExperimentsSummary);
    attachProjAccordionClickHandlers("public-project", "public-toggle-", "collapsepub-", "public-recent-experiments-", loadRecentExperimentsSummary);
    expandFirstProjects();
});
