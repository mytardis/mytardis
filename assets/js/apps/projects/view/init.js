$(document).ready(function() {

    var loadingHTML = "<img src=\"/static/images/ajax-loader.gif\"/><br />";

    // Create a reload event handler
    $("#metadata-pane").on("reload", function() {
        $(this).load("/project/ajax/project_metadata/" + $("#project-id").val() + "/");
    });
});


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

function getFormInputHtml(labelName, name, useTextArea)
{
    var widget;
    if (useTextArea) {
        widget = "<textarea " + "name=\"" + name + "\" id=\"" + name + "\"/>";
    } else {
        widget = "<input type=\"text\" name=\"" + name + "\" value=\"\" id=\"" + name + "\" />";
    }
    var label = "<label for=\"" + name + "\">" + labelName + "</label>";
    return "<div class=\"form-group\">" + label + "<br/>" + widget + "</div>";
}

$(document).on("change", "#schemaselect", function(e) {
    e.preventDefault();

    var $this = $(this);
    var $jqmContentDiv = $this.closest(".modal-body");

    var type = $this.attr("data-type");
    var parentObjectId = $this.attr("data-parent_object_id");
    var href = "/project/ajax/add_" + type + "_parameters/" + parentObjectId + "/?schema_id=" + $this.val();
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
        $("#parameternameselect").before(getFormInputHtml($selectedOption.text(), newElementName, isLong));
        $("#" + newElementName).focus();
    }
    else
    {
        alert("There are no parameters allowed to be added by users in this schema");
    }
});

$(document).on("submit", "#add_metadata_form", function(e) {
    e.preventDefault();

    var form = $(this);
    var contentContainer = form.closest(".modal-body");

    var schemaId = $("#schemaselect").val();
    var type = form.attr("data-type");
    var parentObjectId = form.attr("data-parent_object_id");
    var href = "/project/ajax/add_" + type + "_parameters/" + parentObjectId + "/?schema_id=" + schemaId;

    $.ajax({
        type: "POST",
        url: href,
        data: form.serialize(),
        success: function(data) {
            contentContainer.html(data);
            if (contentContainer.find("form").length === 0) {
                contentContainer.parents(".modal").find(".modal-footer").hide();
            }
            $("#metadata-pane")[0].dispatchEvent(new Event("reload"));
        }
    });

    // Hide the form buttons
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
            $("#metadata-pane")[0].dispatchEvent(new Event("reload"));
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
});

$(document).on("click", ".edit-metadata", function(evt) {
    evt.preventDefault();
    $("#modal-metadata .modal-header .title").text("Edit Metadata");
    loadModalRemoteBody(this, "#modal-metadata");
});

$(document).on("click", "#request-fast-access", function(evt) {
    evt.preventDefault();
    var modal = "#modal-retrieve-files";
    $(modal).find(".modal-footer").hide();
    // Fill with "loading" placeholder content
    $(modal).find(".modal-jobid").html(
        $(modal).find(".loading-placeholder").html()
    );
    $(modal).modal("show");
    $.ajax({
        url: $(this).attr("href"),
        success: function(data, textStatus, jqXHR) {
            $(modal).find(".modal-jobid").html(data.result);
        }
    });
});