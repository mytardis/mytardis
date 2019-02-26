/* tardis/tardis_portal/static/js/jquery/tardis_portal/view_dataset/ready.js */
  
/* eslint global-strict: 0, strict: 0, object-shorthand: 0,
          no-unused-vars: [2, {"vars": "local", "args": "none"}] */

/* global prevFileSelect */

$(document).ready(function() {

    // Create a reload event handler
    $("#metadata-pane").on("reload", function() {
        $(this).load("/ajax/dataset_metadata/" + $("#dataset-id").val() + "/");
        if(prevFileSelect)
        {
            $("#datafile-info").load(prevFileSelect.find(".datafile-info-toggle").attr("href"));
        }
    });

    // load datafiles on page load
    $("#datafiles-pane").load("/ajax/datafile_list/" + $("#dataset-id").val() + "/");

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
        });
    });

    // Reload data file list when we close the upload modal
    $("#modal-upload-files").on("hide", function() {
        $("#datafiles-pane").trigger("reload");
        // Also reload metadata (as it may have been created by the upload)
        $("#metadata-pane").trigger("reload");
    });

    // Set up carousel
    $(".carousel").carousel({
        "interval": 2000
    });
    // Set carousel size
    $("#preview, #preview .carousel-inner").css("width", "320").css("height", "240");

    if ($("#upload-method").val()) {
        $("#upload_button_code").load($("#upload-method-url").val());
    }

    // If the HSM (Hierarchical Storage Management) app is enabled,
    // we can check how many files are online
    $.getJSON("/api/v1/?format=json", function(apiEndpointsData) {
        var hsmEnabled = ("hsm_replica" in apiEndpointsData);
        if (hsmEnabled) {
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
});
