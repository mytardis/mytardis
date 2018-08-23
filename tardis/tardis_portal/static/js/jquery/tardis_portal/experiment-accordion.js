$(".accordion-toggle").click(function(event) {
    var experimentId = $(this).attr("id").replace("toggle", "");

    if (!$("#collapse" + experimentId).hasClass("in")) {
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
    }

    $("#collapse" + experimentId).collapse("toggle");
});

$(document).ready(function() {
    /* Open the first 5 experiments automatically */
    $(".exp-index").each(function() {
        var expIndex = parseInt($(this).val());
        if (expIndex <= 5) {
            $(this).parent().click();
        }
    });
});
