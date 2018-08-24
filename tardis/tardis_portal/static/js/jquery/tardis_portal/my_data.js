/* tardis/tardis_portal/static/js/jquery/tardis_portal/my_data.js */

/* global attachExpAccordionClickHandlers, expandFirstExperiments */

$(document).ready(function() {
    // Load owned exps on page load
    var loadingHTML = "<img src=\"/static/images/ajax-loader.gif\"/><br />";
    $("#myowned").html(loadingHTML);
    $("#myowned").load(
        "/ajax/owned_exps_list/",
        function() {
            attachExpAccordionClickHandlers();
            expandFirstExperiments();
        });

    // Create a reload event handler
    $("#myowned").on("reload", function() {
        $(this).html(loadingHTML);
        $(this).load(
            "/ajax/owned_exps_list/",
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
    $("#myowned").load(href, function() {});
    return false;
});

