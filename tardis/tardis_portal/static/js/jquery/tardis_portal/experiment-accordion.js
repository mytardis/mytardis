/* tardis/tardis_portal/static/js/jquery/tardis_portal/experiment-accordion.js */

/* eslint no-unused-vars: [2, {"vars": "local", "args": "none"}] */

var loadLatestDatasetSummary = function(experimentId) {
    $.ajax({
        url: "/ajax/experiment/" + experimentId + "/latest_dataset",
        type: "GET",
        dataType: "html",
        success: function(data) {
            $("#latest-dataset-" + experimentId).html(data);
        },
        error: function(jqXHR, status) {
            $("#latest-dataset-" + experimentId).html("<p>Failed to retrieve latest dataset summary for exp ID " + experimentId + "</p>");
        }
    });
};

var attachExpAccordionClickHandlers = function() {
    $(".accordion-toggle").click(function(event) {
        var experimentId = $(this).attr("id").replace("toggle", "");
        if (!$("#collapse" + experimentId).hasClass("in")) {
            loadLatestDatasetSummary(experimentId);
        }
        $("#collapse" + experimentId).collapse("toggle");
    });
};

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

$(document).ready(function() {
    attachExpAccordionClickHandlers();
    expandFirstExperiments();
});
