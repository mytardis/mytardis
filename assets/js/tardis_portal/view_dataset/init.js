var loadingHTML = "<img src=\"/static/images/ajax-loader.gif\"/><br />";


// file selectors
jQuery(document).on("click", ".dataset_selector_all", function() {
    $(this).parents(".datafiles").find(".datafile_checkbox").attr("checked", "checked");
});
jQuery(document).on("click", ".dataset_selector_none", function() {
    $(this).parents(".datafiles").find(".datafile_checkbox").removeAttr("checked");
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

// datafile metadata
$(document).on("click", "#datafiles-pane .datafile-info-toggle", function(evt) {
    evt.preventDefault();
    var $this = $(this);
    var $datafileMetadataContainer =
      $("#datafile-info");

    $datafileMetadataContainer.toggle();

    var fileSelect = $this.parents("tr.datafile");
    fileSelect.addClass("file-select");

    var href = $this.attr("href");
    $datafileMetadataContainer.html(loadingHTML);
    $datafileMetadataContainer.load(href, function() {
        $(".df-view-button").on("click", function(e) {
            e.preventDefault();
            $("#df-view-h1").text(this.innerText);
            $("#datafile-app").load(this.href);
            $(this).siblings().each(function() {
                $(this).removeClass("active");
            });
            $(this).addClass("active");
        });
        $("#datafile-app").load($("#df-view-0-url").val());
    });
    $datafileMetadataContainer.show();

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

$(document).on("click", ".page-link", function(event) {
    var href = $(this).attr("href");
    $(this).html(loadingHTML);
    $("#datafiles-pane").load(href, function() {
        $(".dataset_selector_all").unbind("click");
        $(".dataset_selector_none").unbind("click");
        // file selectors
        $(document).find(".dataset_selector_all").on("click", function() {
            $(this).parent().find(".datafile_checkbox").attr("checked", "checked");

        });

        $(document).find(".dataset_selector_none").on("click", function() {
            $(this).parent().find(".datafile_checkbox").removeAttr("checked");

        });
    });
    return false;
});

function filenameSearchHandler(e) {
    // Only care about "Enter" key
    if (e.keyCode !== 13) {
        return;
    }
    // Disable form submit - we'll do that ourselves
    e.preventDefault();
    // Build form submission, and reload pane with results
    var form = $("#filename-search");
    $.ajax({
        "url": form.attr("data-action"),
        "type": form.attr("data-method"),
        "data": form.children("input").serialize(),
        "success": function(data) {
            $("#datafiles-pane").html(data);
        }
    });
    // Show loading indicator
    $("#datafiles-pane").html(loadingHTML);
}
window.filenameSearchHandler = filenameSearchHandler;

$(document).on("click", "input[name$='show_search']", function() {
    var showSearch = $(this).val();
    $(".datafile-pane")
        .each(
            function() {
                var toggle = $(this).siblings(".datafile-list-toggle");
                var loadHtml = "<img src=\"/static/images/ajax-loader.gif\"/><br />";

                var html = $(this).siblings(".datafile-list-toggle").attr("href");
                if (showSearch === "matches") {
                    html = html + "&limit=true";
                } else {
                    html = html.replace("&limit=true", "");
                }
                toggle.attr("href", html);

                if (toggle.hasClass("files_shown")) {
                    $(this).html(loadHtml);
                    $(this).load(html);
                }
            });
    if ($(this).val() === "matches") {
        $(".dataset").hide();
        $(".search_match").show();
        $(".datafile_match").show();
    } else {
        $(".dataset").show();
    }
});
