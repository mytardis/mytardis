/* tardis/tardis_portal/static/js/jquery/tardis_portal/view_experiment/init.js */
  
/* eslint global-strict: 0, strict: 0 */


// file selectors
jQuery(".dataset_selector_all").live("click", function() {
    $(this).parents(".datafiles").find(".datafile_checkbox").attr("checked", "checked");
});
jQuery(".dataset_selector_none").live("click", function() {
    $(this).parents(".datafiles").find(".datafile_checkbox").removeAttr("checked");
});

function get_new_parameter_name(name)
{
    var new_name = name;

    var i = 1;
    while($("[name=" + new_name + "__" + i + "]").length == 1)
    {
        i++;
    }
    return new_name + "__" + i;
}

function get_form_input_html(label, name, use_textarea)
{
    var widget;
    if (use_textarea) {
        widget = "<textarea " + "name=\"" + name + "\" id=\"" + name + "\"/>";
    } else {
        widget = "<input type=\"text\" name=\"" + name + "\" value=\"\" id=\"" + name + "\" />";
    }
    label = "<label for=\"" + name + "\">" + label + "</label>";
    return "<div class=\"fieldWrapper\">" + label + "<br/>" + widget + "</div>";
}

$(".dataset_checkbox").live("click", function( event ) {
    if ($(this).is(":checked")) {
        $(this).parents(".dataset").find(".datafile_checkbox").attr("disabled", true);
        $(this).parents(".dataset").find(".filename_search").attr("disabled", true);
    } else {
        $(this).parents(".dataset").find(".datafile_checkbox").removeAttr("disabled");
        $(this).parents(".dataset").find(".filename_search").removeAttr("disabled");
    }
});

$("#schemaselect").live("change", function(e) {
    e.preventDefault();

    var $this = $(this);
    var $jqm_content_div = $this.closest(".modal-body");

    var type = $this.attr("data-type");
    var parent_object_id = $this.attr("data-parent_object_id");
    var href = "/ajax/add_" + type + "_parameters/" + parent_object_id + "/?schema_id=" + $this.val();
    $.get(href, function(data) {
        $jqm_content_div.html(data);
    });
    return false;
});

$("#add_new_parameter").live("click", function() {
    // assuming whenever add_new_parameter is clicked an option is selected
    var $selected_option = $("#parameternameselect > option:selected");
    var is_long = $selected_option.attr("data-longstring");
    var new_element_name = get_new_parameter_name($selected_option.val());

    if($selected_option.text())
    {
        $("#parameternameselect").before(get_form_input_html($selected_option.text(), new_element_name, is_long));
        $("#" + new_element_name).focus();
    }
    else
    {
        alert("There are no parameters allowed to be added by users in this schema");
    }
});

$("#add_metadata_form").live("submit", function(e) {
    e.preventDefault();

    var form = $(this);
    var contentContainer = form.closest(".modal-body");

    var schema_id = $("#schemaselect").val();
    var type = form.attr("data-type");
    var parent_object_id = form.attr("data-parent_object_id");
    var href = "/ajax/add_" + type + "_parameters/" + parent_object_id + "/?schema_id=" + schema_id;

    $.ajax({
        type: "POST",
        url: href,
        data: form.serialize(),
        success: function(data) {
            contentContainer.html(data);
            if (contentContainer.find("form").length == 0) {
                contentContainer.parents(".modal").find(".modal-footer").hide();
            }
        },
        async: false
    });

    refreshMetadataDisplay();

    form.parents(".modal").find(".modal-footer").hide();
    return false;
});

$("#edit_metadata_form").live("submit", function(e) {
    e.preventDefault();
    var form = $(this);
    var contentContainer = form.closest(".modal-body");

    $.ajax({
        type: "POST",
        url: form.attr("action"),
        data: form.serialize(),
        success: function(data) {
            contentContainer.html(data);
            if (contentContainer.find("form").length == 0) {
                contentContainer.parents(".modal").find(".modal-footer").hide();
            }
        },
        async: false
    });

    refreshMetadataDisplay();

    // Hide the form buttons
    form.parents(".modal").find(".modal-footer").hide();
    return false;
});

var refreshMetadataDisplay = function(hash) {
    $("#experiment-tab-metadata").trigger("experiment-change");
};

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

$(".add-metadata").live("click", function(evt) {
    evt.preventDefault();
    $("#modal-metadata .modal-header .title").text("Add Metadata");
    loadModalRemoteBody(this, "#modal-metadata");
});

$(".edit-metadata").live("click", function(evt) {
    evt.preventDefault();
    $("#modal-metadata .modal-header .title").text("Edit Metadata");
    loadModalRemoteBody(this, "#modal-metadata");
});

$("#modal-metadata .submit-button").click(function() {
    $("#modal-metadata .modal-body form").submit();
});
