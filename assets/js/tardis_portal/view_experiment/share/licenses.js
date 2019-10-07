/* licenses.js */
/* global _, async, Mustache */

// Memoized AJAX call (which should make things snappier) to get license JSON
var loadLicenses = async.memoize(function(publicAccess, callback) {
    $.ajax({
        url: "/ajax/license/list?public_access=" + publicAccess,
        dataType: "json",
        success: callback
    });
});

var selectLicenseOption = function(value) {
    var selectedOption = $(`.license-option input[value="${value}"]`)
        .parents(".license-option");
    selectedOption.find(".use-button").addClass("disabled");
    selectedOption.find(".use-button").text("Selected");
};

export var populateLicenseOptions = function(publicAccess, markSameLicense) {
    loadLicenses(publicAccess, function(licenses) {
        $("#license-options").empty();
        _(licenses).each(function(license) {
            $("#license-options").append(
                Mustache.to_html(
                    Mustache.TEMPLATES["tardis_portal/license_selector"],
                    license, Mustache.TEMPLATES)
            );
            if (markSameLicense) {
                selectLicenseOption($(`form input[name="${license}"]`).val());
            }
        });
    });
};

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
    $("#legal-section").show();
    $("#license-options").hide();
});

$(document).on("click", "#reselect-license", function() {
    $("#selected-license-text").html("");
    $("#license-options").show();
    $("#legal-section").hide();
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
    $("#legal-section").show();
    $("#license-options").hide();
});

$(document).on("click", "#reselect-license", function() {
    $("#selected-license-text").html("");
    $("#license-options").show();
    $("#legal-section").hide();
});
