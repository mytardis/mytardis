$(document).ready(function() {

    // Create a reload event handler
    $("#metadata-pane").on("reload", function() {
        $(this).load("/ajax/dataset_metadata/" + $("#dataset-id").val() + "/");
    });

    // load datafiles on page load
    $("#datafiles-pane").load(
        "/ajax/datafile_list/" + $("#dataset-id").val() + "/", function() {
            $(".archived-file").tooltip({"title": "This file is archived."});
            $("a.archived-file").on("click", function(evt) {
                evt.preventDefault();
            });
        });

    // Create a reload event handler
    $("#datafiles-pane").on("reload", function() {
        $(this).load("/ajax/datafile_list/" + $("#dataset-id").val() + "/", function() {
            var datafileCount = parseInt($("#datafile-count").val());
            var fileCountString = "" + datafileCount + " File";
            if (datafileCount !== 1) {
                fileCountString += "s";
            }
            $("#total-count").html(fileCountString);
            // Reset progress bar after datafiles-pane has reloaded:
            $("#progress .progress-bar").css("width", "0%");

            $(".archived-file").tooltip({"title": "This file is archived."});
            $("a.archived-file").on("click", function(evt) {
                evt.preventDefault();
            });
        });
    });

    // Reload data file list when we close the upload modal
    $("#modal-upload-files").on("hide", function() {
        var reloadEvent = new Event("reload");
        $("#datafiles-pane")[0].dispatchEvent(reloadEvent);
        // Also reload metadata (as it may have been created by the upload)
        reloadEvent = new Event("reload");
        $("#metadata-pane")[0].dispatchEvent(reloadEvent);
    });

    // Set up carousel
    $(".carousel").carousel({
        "interval": 2000
    });
    // Set carousel size
    $("#preview, #preview .carousel-inner").css("width", "320").css("height", "240");

    if ($("#upload-method").val() === true) {
        $("#upload_button_code").load($("#upload-method-url").val());
    }

    // If the HSM (Hierarchical Storage Management) app is enabled,
    // we can check how many files are online
    if ($("#hsm-enabled").val() === "True") {
        $(".datafile-count-badge").html(
            "<i class=\"fa fa-spinner fa-spin\"></i>&nbsp; " +
            $("#datafile-count").val());
        var onlineFilesCountUrl = "/ajax/dataset_online_files_count/" +
            $("#dataset-id").val() + "/";
        $.getJSON(onlineFilesCountUrl, function(data) {
            var datafileCountBadgeText = "" + data.total_files;
            if (data.online_files < data.total_files) {
                datafileCountBadgeText = "" + data.online_files +
                    " online / " + data.total_files + " files";
            }
            $(".datafile-count-badge").html(
                "<i class=\"fa fa-file\"></i>&nbsp; " + datafileCountBadgeText);
        });
    }
});
