/* licenses.js */

export var selectLicenseOption = function(value) {
    var selectedOption = $(`.license-option input[value="${value}"]`)
        .parents(".license-option");
    selectedOption.find(".use-button").attr("disabled", true);
    selectedOption.find(".use-button").text("Selected");
};

$(document).on("click", "#license-options .use-button", function(evt) {
    // Get the selected ID from hidden input
    var id = $(this).parents(".license-option").find("input.license-id").val();
    // Set the licence ID for the form
    $(this).parents("form").find("input[name=license]").val(id);
    // Enable all buttons, then disable the one we selected
    $(this).parents("#license-options")
        .find(".use-button")
        .attr("disabled", false)
        .text("Use");
    $(this).attr("disabled", true);
    $(this).text("Selected");
    // Hide any current messages
    $(this).parents(".tab-pane").find(".alert .close").click();
    // Show confirmation window
    $("#selected-license-text").html($(this).parents(".license-option")
        .find(".col-md-10").html());
    $("#license-options").hide();
    $("#legal-section").show();
    $("#confirm-license-btn-group").show();
});

$(document).on("click", "#reselect-license", function() {
    $("#selected-license-text").html("");
    $("#license-options").show();
    $("#legal-section").hide();
    $("#confirm-license-btn-group").hide();
});

$(document).on("click", "#license-options .use-button", function(evt) {
    // Get the selected ID from hidden input
    var id = $(this).parents(".license-option").find("input.license-id").val();
    // Set the licence ID for the form
    $(this).parents("form").find("input[name=license]").val(id);
    // Enable all buttons, then disable the one we selected
    $(this).parents("#license-options")
        .find(".use-button")
        .removeClass("disabled")
        .text("Use");
    $(this).addClass("disabled");
    $(this).text("Selected");
    // Hide any current messages
    $(this).parents(".tab-pane").find(".alert .close").click();
    // Show confirmation window
    $("#selected-license-text").html($(this).parents(".license-option")
        .find(".col-md-10").html());
    $("#license-options").hide();
    $("#legal-section").show();
    $("#confirm-license-btn-group").show();
});

$(document).on("click", "#reselect-license", function() {
    $("#selected-license-text").html("");
    $("#license-options").show();
    $("#legal-section").hide();
    $("#confirm-license-btn-group").hide();
});
