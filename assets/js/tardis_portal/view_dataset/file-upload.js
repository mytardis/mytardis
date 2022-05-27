/* global showMsg */

import React from "react";
import ReactDOM from "react-dom";
import TreeView from "../../apps/tree_view/components/TreeView";

require("imports-loader?define=>false&exports=>false!blueimp-file-upload/js/vendor/jquery.ui.widget");
require("imports-loader?define=>false&exports=>false!blueimp-file-upload/js/jquery.fileupload");
require("imports-loader?define=>false&exports=>false!blueimp-file-upload/js/jquery.iframe-transport");

// https://docs.djangoproject.com/en/3.1/ref/csrf/
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

$(function() {
    $("#dropzone").hide();
    $("#fileupload").fileupload({
        dataType: "json",
        headers: {"X-CSRFToken": getCookie("csrftoken")},
        done: function(e, data) {
            var reloadEvent = new Event("reload");
            $("#datafiles-pane")[0].dispatchEvent(reloadEvent);
            var length = data.files.length;
            for (var i = 0; i < length; i++) {
                showMsg.success(data.files[i].name + " was successfully uploaded");
                // need to change notification to show multiple, not replace existing ones
            }
        },
        dropZone: $(".dropzone")
    });
    $("#datafiles-pane").bind("drop dragover", function(e) {
        e.preventDefault();
    });
    $("#fileupload").bind("fileuploadsubmit", function(e, data) {
        var jsondata = {
            dataset: "/api/v1/dataset/" + $("#dataset-id").val() + "/",
            filename: data.files[0].name,
            size: data.files[0].size,
            mimetype: data.files[0].type
        };
        data.formData = {"json_data": JSON.stringify(jsondata)};
    }).on("fileuploadprogressall", function(e, data) {
        var progress = parseInt(data.loaded / data.total * 100, 10);
        $("#progress .progress-bar").css(
            "width",
            progress + "%"
        );
        if (progress === 100) {
            setTimeout(function() {
                var reloadEvent = new Event("reload");
                $("#datafiles-pane")[0].dispatchEvent(reloadEvent);
                ReactDOM.render(
                    React.createElement(
                        TreeView, {
                            datasetId: $("#dataset-id").val(),
                            modified: String(Date.now())
                        }, null
                    ),
                    $("#tree_view")[0]
                );
            }, 500);
        }
    });
});

var showDropzone = function() {
    $("#datafiles-pane").hide();
    $("#dropzone").show();
};

var hideDropzone = function() {
    $("#datafiles-pane").show();
    $("#dropzone").hide();
};

// eslint-disable-next-line complexity
$(document).bind("dragover", function(e) {
    var dropZone = $(".dropzone"),
        timeout = window.dropZoneTimeout;
    if (!timeout) {
        showDropzone();
    } else {
        clearTimeout(timeout);
    }
    var found = false,
        node = e.target;
    do {
        if (node === dropZone[0]) {
            found = true;
            break;
        }
        node = node.parentNode;
    } while (node !== null);
    if (found) {
        dropZone.addClass("hover");
    } else {
        dropZone.removeClass("hover");
    }
    window.dropZoneTimeout = setTimeout(function() {
        window.dropZoneTimeout = null;
        hideDropzone();
    }, 100);
});
