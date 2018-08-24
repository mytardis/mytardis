/* tardis/tardis_portal/static/js/jquery/tardis_portal/shared.js */

/* global attachExpAccordionClickHandlers, expandFirstExperiments */

$(document).ready(function() {
    // Load shared exps on page load
    var loadingHTML = "<img src=\"/static/images/ajax-loader.gif\"/><br />";
    $("#myshared").html(loadingHTML);
    $("#myshared").load(
        "/ajax/shared_exps_list/",
        function() {
            attachExpAccordionClickHandlers();
            expandFirstExperiments();
        });

    // Create a reload event handler
    $("#myshared").on("reload", function() {
        $(this).html(loadingHTML);
        $(this).load(
            "/ajax/shared_exps_list/",
            function() {
                attachExpAccordionClickHandlers();
                expandFirstExperiments();
            });
    });
});

$(document).on("click", ".pagelink", function() {
    var loadingHTML = "<img src=\"/static/images/ajax-loader.gif\"/><br />";
    var href = $(this).attr("href");
    $(this).html(loadingHTML);
    $("#myshared").load(href, function() {});
    return false;
});

