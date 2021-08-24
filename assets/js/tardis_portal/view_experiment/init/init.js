// file selectors
jQuery(document).on("click", ".dataset_selector_all", function() {
    $(this).parents(".datafiles").find(".datafile_checkbox").attr("checked", "checked");
});
jQuery(document).on("click", ".dataset_selector_none", function() {
    $(this).parents(".datafiles").find(".datafile_checkbox").removeAttr("checked");
});

import { loadExpTabPane } from "../experiment-tabs.js";
// import { getDatasetsForExperiment} from "../dataset-tiles";

function getNewParameterName(name)
{
    var newName = name;

    var i = 1;
    while($("[name=" + newName + "__" + i + "]").length === 1)
    {
        i++;
    }
    return newName + "__" + i;
}

function getFormInputHtml(label, name, useTextArea)
{
    var widget;
    if (useTextArea) {
        widget = "<textarea class='form-control' " + "name=\"" + name + "\" id=\"" + name + "\"/>";
    } else {
        widget = "<input class='form-control' type=\"text\" name=\"" + name + "\" value=\"\" id=\"" + name + "\" />";
    }
    label = "<label class='form-label' for=\"" + name + "\">" + label + "</label>";
    return "<div class='row mb-3'><div class='col-md-12'>" + label + widget + "</div></div>";
}

$(document).on("click", ".dataset_checkbox", function( event ) {
    if ($(this).is(":checked")) {
        $(this).parents(".dataset").find(".datafile_checkbox").attr("disabled", true);
        $(this).parents(".dataset").find(".filename_search").attr("disabled", true);
    } else {
        $(this).parents(".dataset").find(".datafile_checkbox").removeAttr("disabled");
        $(this).parents(".dataset").find(".filename_search").removeAttr("disabled");
    }
});

$(document).on("change", "#schemaselect", function(e) {
    e.preventDefault();

    var $this = $(this);
    var $jqmContentDiv = $this.closest(".modal-body");

    var type = $this.attr("data-type");
    var parentObjectId = $this.attr("data-parent_object_id");
    var href = "/ajax/add_" + type + "_parameters/" + parentObjectId + "/?schema_id=" + $this.val();
    $.get(href, function(data) {
        $jqmContentDiv.html(data);
    });
    return false;
});

$(document).on("click", "#add_new_parameter", function() {
    // assuming whenever add_new_parameter is clicked an option is selected
    var $selectedOption = $("#parameternameselect > option:selected");
    var isLong = $selectedOption.attr("data-longstring");
    var newElementName = getNewParameterName($selectedOption.val());

    if($selectedOption.text())
    {
        $("#parameternameselect").parent().parent().before(getFormInputHtml($selectedOption.text(), newElementName, isLong));
        $("#" + newElementName).focus();
    }
    else
    {
        alert("There are no parameters allowed to be added by users in this schema");
    }
});

var refreshMetadataDisplay = function() {
    loadExpTabPane("metadata");
};

$(document).on("submit", "#add_metadata_form", function(e) {
    e.preventDefault();

    var form = $(this);
    var contentContainer = form.closest(".modal-body");

    var schemaId = $("#schemaselect").val();
    var type = form.attr("data-type");
    var parentObjectId = form.attr("data-parent_object_id");
    var href = "/ajax/add_" + type + "_parameters/" + parentObjectId + "/?schema_id=" + schemaId;

    $.ajax({
        type: "POST",
        url: href,
        data: form.serialize(),
        success: function(data) {
            contentContainer.html(data);
            if (contentContainer.find("form").length === 0) {
                contentContainer.parents(".modal").find(".modal-footer").hide();
            }
            refreshMetadataDisplay();
        }
    });

    form.parents(".modal").find(".modal-footer").hide();
    return false;
});

$(document).on("submit", "#edit_metadata_form", function(e) {
    e.preventDefault();
    var form = $(this);
    var contentContainer = form.closest(".modal-body");

    $.ajax({
        type: "POST",
        url: form.attr("action"),
        data: form.serialize(),
        success: function(data) {
            contentContainer.html(data);
            if (contentContainer.find("form").length === 0) {
                contentContainer.parents(".modal").find(".modal-footer").hide();
            }
            refreshMetadataDisplay();
        }
    });

    // Hide the form buttons
    form.parents(".modal").find(".modal-footer").hide();
    return false;
});

var loadModalRemoteBody = function(trigger, modal) {
    // Hide save buttons
    $(modal).find(".modal-footer").hide();
    // Fill with "loading" placeholder content
    $(modal).find(".modal-body").html(
        $(modal).find(".loading-placeholder").html()
    );
    $(modal).modal("show");
    $.ajax({
        url: $(trigger).attr("href"),
        success: function(data, textStatus, jqXHR) {
            $(modal).find(".modal-body").html(data);
            $(modal).find(".modal-footer").show();
        }
    });
};

$(document).on("click", ".add-metadata", function(evt) {
    evt.preventDefault();
    $("#modal-metadata .modal-header .title").text("Add Metadata");
    loadModalRemoteBody(this, "#modal-metadata");
    $("#add_edit_metadata_save_button").attr("form", "add_metadata_form");
});

$(document).on("click", ".edit-metadata", function(evt) {
    evt.preventDefault();
    $("#modal-metadata .modal-header .title").text("Edit Metadata");
    loadModalRemoteBody(this, "#modal-metadata");
    $("#add_edit_metadata_save_button").attr("form", "edit_metadata_form");
});

$("#modal-metadata .submit-button").click(function() {
    $("#modal-metadata .modal-body form").submit();
});

/*$(document).on("change", "select[name='experiment_id']", function(evt) {
    evt.preventDefault();
    var experimentId = $(this).val();
    // eslint-disable-next-line no-unused-vars
    var otherDatasetTiles = getDatasetsForExperiment(experimentId);
});*/

