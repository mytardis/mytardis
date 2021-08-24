/**
 * Loads recent datasets from a given experiment into a div
 * @param {string} divIdPrefix - Prefix of the div element's ID, e.g. "latest-dataset-"
 * @param {string} experimentId - The database ID of the experiment to load the latest dataset
 */
// eslint-disable-next-line no-unused-vars
var loadLatestDatasetSummary = function(divIdPrefix, experimentId) {
    $.ajax({
        url: "/ajax/experiment/" + experimentId + "/latest_dataset",
        type: "GET",
        dataType: "html",
        success: function(data) {
            $("#" + divIdPrefix + experimentId).html(data);
        },
        error: function(jqXHR, status) {
            $("#" + divIdPrefix + experimentId).html("<p>Failed to retrieve latest dataset summary for exp ID " + experimentId + "</p>");
        }
    });
};

/**
 * Loads recent datasets from a given experiment into a div
 * @param {string} divIdPrefix - Prefix of the div element's ID, e.g. "public-recent-datasets-"
 * @param {string} experimentId - The database ID of the experiment to load recent datasets from
 */
// eslint-disable-next-line no-unused-vars
var loadRecentDatasetsSummary = function(divIdPrefix, experimentId) {
    $.ajax({
        url: "/ajax/experiment/" + experimentId + "/recent_datasets",
        type: "GET",
        dataType: "html",
        success: function(data) {
            $("#" + divIdPrefix + experimentId).html(data);
        },
        error: function(jqXHR, status) {
            $("#" + divIdPrefix + experimentId).html("<p>Failed to retrieve recent datasets summary for exp ID " + experimentId + "</p>");
        }
    });
};

/**
 * Attaches click handlers to the experiment accordion elements.
 * @param {string} accordionToggleClass - Used to select the accordion-toggle elements to add click handlers to
 * @param {string} accordionToggleIdPrefix - Prefix of the accordion-toggle element's ID, e.g. "toggle-"
 * @param {string} accordionBodyIdPrefix - Prefix of the card-body element's ID, e.g. "collapse-"
 * @param {string} divIdPrefix - Prefix of the div element's ID, e.g. "public-recent-datasets-"
 * @param {function} loadDatasetsSummary - Either loadLatestDatasetSummary or loadRecentDatasetsSummary
 */
// eslint-disable-next-line no-unused-vars
var attachExpAccordionClickHandlers = function(accordionToggleClass, accordionToggleIdPrefix, accordionBodyIdPrefix, divIdPrefix, loadDatasetsSummary) {
    $("." + accordionToggleClass).on("click", function(event) {
        var experimentId = $(this).attr("id").replace(accordionToggleIdPrefix, "");
        if (!$("#" + accordionBodyIdPrefix + experimentId).hasClass("in")) {
            loadDatasetsSummary(divIdPrefix, experimentId);
        }
        $("#" + accordionBodyIdPrefix + experimentId).collapse("toggle");
    });
};

// eslint-disable-next-line no-unused-vars
var expandFirstExperiments = function() {
    // Expand the first experiments' accordion blocks automatically
    $(".exp-index").each(function() {
        var expsExpandAccordion = parseInt($("#exps-expand-accordion").val());
        var expIndex = parseInt($(this).val());
        if (expIndex <= expsExpandAccordion) {
            $(this).parent().click();
        }
    });
};

var handleExpAccordionLink = function(e) {
    window.location.href = $(e.target).attr("href");
    e.preventDefault();
    e.stopPropagation();
    return false;
};

export {
    attachExpAccordionClickHandlers,
    loadLatestDatasetSummary,
    expandFirstExperiments,
    loadRecentDatasetsSummary,
    handleExpAccordionLink
};
