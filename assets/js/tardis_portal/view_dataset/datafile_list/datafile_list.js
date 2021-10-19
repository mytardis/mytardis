$(document).ready(function() {
    function getCheckboxHtml(datafile, hasDownloadPermissions) {
        if (datafile.has_download_permissions && datafile.verified && datafile.is_online) {
            return "<input type=\"checkbox\" style=\"\" " +
                "class=\"datafile_checkbox\" name=\"datafile\" " +
                "value=\"" + datafile.id + "\"/>";
        }
        return "";
    }

    /*
     * Return HTML to display clickable filename for DataFile
     */
    function getViewHyperlink(datafile) {
        return "<a class=\"filelink datafile_name\"" +
            "href=\"" + datafile.view_url + "\"" +
            "title=\"View\"" +
            "target=\"_blank\">" + datafile.filename + "</a>";
    }

    /*
     * Return HTML to display unclickable filename for DataFile
     */
    function getUnclickableFilenameHtml(datafile) {
        if (datafile.verified) {
            return "<span class=\"datafile_name" +
                (datafile.is_online ? "" : " archived-file") +
                "\">" + datafile.filename + "</span>";
        }
        // Unverified files are displayed in red:
        return "<span class=\"datafile_name\" style=\"color:red;\">" +
            datafile.filename + "</span>";
    }

    /*
     * Return HTML to display file size
     */
    function getFileSizeHtml(datafile) {
        if (datafile.formatted_size) {
            return "<span " +
                (datafile.is_online ? "" : "class=\"archived-file\" ") +
                "style=\"margin-right: 5px" +
                (datafile.verified ? "" : " color:red;") +
                "\"" + ">" +
                " (" + datafile.formatted_size + ")" +
                "</span>";
        }
        return "";
    }

    /*
     * Return HTML to display file size
     */
    function getUnverifiedOrOfflineHtml(datafile) {
        if (!datafile.verified) {
            return " <span style=\"margin-right: 5px; color:red;\">(unverified)</span>";
        }
        if (!datafile.is_online) {
            return " <span class=\"archived-file\" style=\"margin-right: 5px;\">(archived)</span>";
        }
        return "";
    }

    /*
     * Return HTML to display DataFile filename, annotated with
     * file size, verified status, and online status.
     *
     * Make it a hyperlink if the DataFile has a view URL.
     */
    // eslint-disable-next-line complexity
    function getAnnotatedFilenameHtml(datafile, hasDownloadPermissions) {
        var filenameHtml = "";
        if (datafile.has_download_permissions && datafile.view_url && datafile.verified && datafile.is_online) {
            filenameHtml = getViewHyperlink(datafile);
        }
        else {
            filenameHtml = getUnclickableFilenameHtml(datafile);
        }
        filenameHtml += getFileSizeHtml(datafile);
        filenameHtml += getUnverifiedOrOfflineHtml(datafile);
        return filenameHtml;
    }

    function getDownloadButtonHtml(datafile) {
        return "<a class=\"btn btn-default btn-sm\" " +
            "   title=\"Download\" " +
            "   href=\"" + datafile.download_url + "\">" +
            "  <i class=\"fa fa-download fa-lg\"></i>" +
            "</a>";
    }

    function getRecallButtonHtml(datafile) {
        var recallButtonHtml = "<button " +
            "class=\"btn btn-default btn-sm recall-datafile\" " +
            "type=\"button\" title=\"Recall\" ";
        if (datafile.recall_url) {
            recallButtonHtml += "data-toggle=\"tooltip\" " +
                "data-recall-url=\"" + datafile.recall_url + "\"" +
                "style=\"pointer-events: auto;\"";
        }
        else {
            recallButtonHtml += "disabled";
        }
        recallButtonHtml += ">";
        recallButtonHtml += "<i class=\"fa fa-undo fa-lg\"></i>";
        recallButtonHtml += "</button>";
        return recallButtonHtml;
    }

    function getAddMetadataButtonHtml(datafile, hasWritePermissions, immutable) {
        if (datafile.has_write_permissions && !immutable) {
            return "<a title=\"Add Metadata\" " +
               "href=\"/ajax/add_datafile_parameters/" + datafile.id + "/\" " +
               "data-toggle_selector=\"#datafile_metadata_toggle_" + datafile.id + "\"" +
               "class=\"btn btn-default btn-sm add-metadata\">" +
                "<i class=\"fa fa-plus fa-lg\"></i>" +
                "</a>";
        }
        return "";
    }

    function getShowHideMetadataButtonHtml(datafile) {
        return "<a id=\"datafile_metadata_toggle_" + datafile.id + "\" " +
            "title=\"Show/Hide Metadata\" " +
            "class=\"btn btn-default btn-sm datafile-info-toggle metadata_hidden\" " +
            "href=\"/ajax/datafile_details/" + datafile.id + "/\">" +
            "<i class=\"fa fa-list fa-lg\"></i>" +
            "</a>";
    }

    function getButtonsHtml(datafile, hasDownloadPermissions, hasWritePermissions, immutable) {
        var datafileButtonsHtml = "";
        if (datafile.has_download_permissions && datafile.verified) {
            if (datafile.is_online) {
                datafileButtonsHtml += getDownloadButtonHtml(datafile);
            }
            else {
                datafileButtonsHtml += getRecallButtonHtml(datafile);
            }
        }

        datafileButtonsHtml += getAddMetadataButtonHtml(datafile, hasWritePermissions, immutable);

        datafileButtonsHtml += getShowHideMetadataButtonHtml(datafile);

        return datafileButtonsHtml;
    }
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
        var onlineFilesCountUrl = "/api/v1/hsm_dataset/" +
            $("#dataset-id").val() + "/count/";
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
    function getlistHTML(pageNumber) {
        $.getJSON(
            "/ajax/datafile_list/" + $("#dataset-id").val() + "?page=" + pageNumber + "&format=json",
            function(data) {
                $.each(data.datafiles, function(datafileIndex, datafile) {

                    var checkboxHtml = getCheckboxHtml(datafile, data.has_download_permissions);
                    $("#datafile-checkbox-" + datafile.id).html(checkboxHtml);

                    var annotatedFilenameHtml = getAnnotatedFilenameHtml(datafile, data.has_download_permissions);
                    $("#datafile-name-" + datafile.id).html(annotatedFilenameHtml);

                    $("#datafile-name-" + datafile.id + " .archived-file").tooltip({
                        "title":
                        "This file is archived. " +
                        "Press the Recall button to request a download link via email."
                    });

                    var buttonsHtml = getButtonsHtml(
                        datafile, data.has_download_permissions, data.has_write_permissions, data.immutable);
                    $("#datafile-buttons-" + datafile.id).html(buttonsHtml);

                    $("#datafile-buttons-" + datafile.id + " .recall-datafile").on("click", function(evt) {
                        var recallUrl = $(this).data("recall-url");
                        var recallButton = $(this);
                        $.get(recallUrl)
                            .done(function() {
                                // Don't add disabled attribute, because that disables tooltips
                                // Instead, add disabled CSS class and remove click handler
                                recallButton.addClass("disabled");
                                recallButton.off("click");
                                recallButton.html(
                                    "<i class=\"fa fa-spinner fa-spin fa-lg\"></i>");
                                recallButton.attr(
                                    "title",
                                    "An email will be sent when the recall is complete");
                                recallButton.tooltip();
                            })
                            .fail(function() {
                                // Don't add disabled attribute, because that disables tooltips
                                // Instead, add disabled CSS class and remove click handler
                                recallButton.addClass("disabled");
                                recallButton.off("click");
                                recallButton.attr("title", "Recall request failed");
                                recallButton.tooltip();
                            });
                    });
                });
            }
        );
    }
    getlistHTML(0);
    $(document).on("click", "ul.pagination li a", function(event) {
        event.preventDefault();
        getlistHTML(this.href.split("=")[1]);
    });
});
