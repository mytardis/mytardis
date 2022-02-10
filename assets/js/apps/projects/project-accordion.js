/**
 * Loads recent experiments from a given project into a div
 * @param {string} divIdPrefix - Prefix of the div element's ID, e.g. "latest-experiment-"
 * @param {string} projectId - The database ID of the project to load the latest experiment
 */
// eslint-disable-next-line no-unused-vars
var loadLatestExperimentSummary = function(divIdPrefix, projectId) {
    $.ajax({
        url: "/project/ajax/" + projectId + "/latest_experiment",
        type: "GET",
        dataType: "html",
        success: function(data) {
            $("#" + divIdPrefix + projectId).html(data);
        },
        error: function(jqXHR, status) {
            $("#" + divIdPrefix + projectId).html("<p>Failed to retrieve latest experiment summary for proj ID " + projectId + "</p>");
        }
    });
};

/**
 * Loads recent experiments from a given project into a div
 * @param {string} divIdPrefix - Prefix of the div element's ID, e.g. "public-recent-experiments-"
 * @param {string} projectId - The database ID of the project to load recent experiments from
 */
// eslint-disable-next-line no-unused-vars
var loadRecentExperimentsSummary = function(divIdPrefix, projectId) {
    $.ajax({
        url: "/project/ajax/" + projectId + "/recent_experiments",
        type: "GET",
        dataType: "html",
        success: function(data) {
            $("#" + divIdPrefix + projectId).html(data);
        },
        error: function(jqXHR, status) {
            $("#" + divIdPrefix + projectId).html("<p>Failed to retrieve recent experiments summary for proj ID " + projectId + "</p>");
        }
    });
};

/**
 * Attaches click handlers to the project accordion elements.
 * @param {string} accordionToggleClass - Used to select the accordion-toggle elements to add click handlers to
 * @param {string} accordionToggleIdPrefix - Prefix of the accordion-toggle element's ID, e.g. "toggle-"
 * @param {string} accordionBodyIdPrefix - Prefix of the card-body element's ID, e.g. "collapse-"
 * @param {string} divIdPrefix - Prefix of the div element's ID, e.g. "public-recent-experiments-"
 * @param {function} loadExperimentsSummary - Either loadLatestExperimentSummary or loadRecentExperimentsSummary
 */
// eslint-disable-next-line no-unused-vars
var attachProjAccordionClickHandlers = function(accordionToggleClass, accordionToggleIdPrefix, accordionBodyIdPrefix, divIdPrefix, loadDatasetsSummary) {
    $("." + accordionToggleClass).click(function(event) {
        var projectId = $(this).attr("id").replace(accordionToggleIdPrefix, "");
        if (!$("#" + accordionBodyIdPrefix + projectId).hasClass("in")) {
            loadExperimentsSummary(divIdPrefix, projectId);
        }
        $("#" + accordionBodyIdPrefix + projectId).collapse("toggle");
    });
};

// eslint-disable-next-line no-unused-vars
var expandFirstProjects = function() {
    // Expand the first projects accordion blocks automatically
    $(".proj-index").each(function() {
        var projExpandAccordion = parseInt($("#proj-expand-accordion").val());
        var projIndex = parseInt($(this).val());
        if (projIndex <= projExpandAccordion) {
            $(this).parent().click();
        }
    });
};
export {attachProjAccordionClickHandlers, loadLatestExperimentSummary, expandFirstProjects, loadRecentExperimentsSummary};
