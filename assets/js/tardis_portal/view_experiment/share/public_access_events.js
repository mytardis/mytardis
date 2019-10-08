/* public access events */
/* global _, Mustache */

import { loadExpTabPane } from "../experiment-tabs.js";
import { populateLicenseOptions } from "./licenses.js";
import { selectLicenseOption } from "./licenses.js";

export var addPublicAccessEvents = function() {
    $(document).on("change", "#publishing-consent", function() {
        // (submit disabled) <=> !(consent checked)
        $("#legal-section .submit-button").prop("disabled", !$(this).prop("checked"));
    });

    // Disable submit button (as consent checkbox should start unchecked)
    var changeEvent = new Event("change");
    $("#publishing-consent")[0].dispatchEvent(changeEvent);

    $(document).on("click", "#legal-section .submit-button", function() {
        // Submit form
        var submitEvent = new Event("submit");
        $("form.experiment-rights")[0].dispatchEvent(submitEvent);
        $("#legal-section").hide();
    });

    $(document).on("click", "#legal-section .cancel-button", function() {
        // Just refresh this tab pane to reset previous values
        loadExpTabPane("sharing");
        $("#legal-section").modal("hide");
    });

    /* Public Access selector logic */
    var publicAccessSelector = $("select[name=public_access]");
    // Remember the original value
    publicAccessSelector.prop("originalValue", publicAccessSelector.val());
    // Change licence options when the public access changes.
    publicAccessSelector.change(function() {
        populateLicenseOptions(
            $(this).val(),
            // So we can change public access levels without necessarilly changing
            // licences, mark the current licence as selected only if the public
            // access level is still the original.
            $(this).prop("originalValue") === $(this).val()
        );
    });
    // Set default state:
    populateLicenseOptions($("select[name=public_access]").val(), true);
    // A Django form is supplied by the view method, which includes some
    // hidden inputs, including #id_license:
    selectLicenseOption($("#id_license").val());

    $("form.experiment-rights").submit(function(evt) {
        evt.preventDefault();
        var form = $(evt.target);

        // Get data for success message
        var templateData = _.reduce(form.serializeArray(), function(obj, v) {
            obj[v.name] = v.value;
            return obj;
        }, {});
        templateData.changedAccess =
            (templateData.public_access !==
              $("select[name=public_access]").prop("originalValue"));

        // Submit form
        $.ajax({
            type: form.attr("method"),
            url: form.attr("action"),
            data: form.serialize(),
            success: function(data) {
                var thisModal = $(form).parents(".modal-body");
                // Load new values into pane
                thisModal.html(data);
                // Show update message
                $("#legal-section").hide();

                $("#choose-rights-message").html(
                    Mustache.to_html(
                        Mustache.TEMPLATES["tardis_portal/rights_update_message"],
                        templateData, Mustache.TEMPLATES)
                );

                populateLicenseOptions(templateData.public_access, true);

                // update badge on view experiment page
                $("#experiment-public-access-badge").load("public_access_badge/");
            },
            error: function(jqXHR, textStatus, errorThrown) {
                var errorData = {"message": errorThrown};
                errorData[textStatus] = true;
                // Show error message
                $("#choose-rights-message").html(
                    Mustache.to_html(
                        Mustache.TEMPLATES["tardis_portal/ajax_error"],
                        errorData, Mustache.TEMPLATES)
                );
            }
        });
    });
};
