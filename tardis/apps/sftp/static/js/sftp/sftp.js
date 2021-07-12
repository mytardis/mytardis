var sftp = (function() {
    function createKeyAlert(msg, level) {
        return "<div id='keyTable' class='alert alert-block alert-" + level + "'>\
        <span class='message'>" + msg + "</span> \
        </div>";
    }

    function addKeyRow(rowData) {
        return "<tr id='keyRow" + rowData.id + "'>\
          <td style='padding: 16px 20px'>\
              <div class='float-start'>\
                <strong>" + rowData.name + "</strong><br>\
                <span>Type: " + rowData.key_type.toUpperCase() + "</span><br>\
                <span style='word-break: break-all;'>Fingerprint: " + rowData.fingerprint + "</span><br>\
                <span>Date added: " + rowData.added + "</span>\
              </div>\
            <div class='text-right float-end'>\
              <button id='delete-btn' class='btn btn-danger' \
                      onclick='sftp.handleKeyDelete(" + rowData.id + ")'>\
                <i class='fa fa-trash'></i>\
                Delete\
              </button>\
          </td></tr>";
    }

    function createKeyTable(keyData) {
        var table = $(document.createElement("table"))
            .addClass("table table-bordered")
            .attr("id", "keyTable")
            .append($("<thead><tr><th><strong>Keys</strong></th></tr></thead>"));

        return keyData.reduce(function(acc, key) {
            return acc.append(addKeyRow(key));
        }, table);
    }

    function loadKeyTable(clear) {
        if (clear) {
            $("#keyTable").replaceWith(
                "<div id='keyTable'><span><i class='fa fa-2x fa-spinner fa-pulse'</i> Loading keys...</span></div>"
            );
        }

        $.ajax(
            "/api/v1/sftp_publickey/"
        ).done(function(json, _textStatus, _jqXHR) {
            var objs = json.objects;
            if (objs.length > 0) {
                $("#keyTable").replaceWith(createKeyTable(objs));
            } else {
                $("#keyTable").replaceWith(createKeyAlert(
                    "You don't have any public keys registered. Please add keys using the Add key button above.",
                    "warning"
                ));
            }
        }).fail(function(_jqXHR, _textStatus, err) {
            throw "Error loading SSH keys:\n" + err;
        });
    }

    function handleKeyDelete(keyId) {
        $.ajax(
            "/api/v1/sftp_publickey/" + keyId,
            {
                method: "DELETE",
                headers: {
                    "X-CSRFToken": $.cookie("csrftoken")
                }
            }
        ).done(function(data, textStatus, _jqXHR) {
            loadKeyTable(true);
        }).fail(function(jqXHR, textStatus, err) {
            throw "SSH key delete error:\n" + err;
        });
    }

    function addKey() {
        try {
            var formData = $("#keyAddForm")
                .serializeArray()
                .reduce(function(acc, x) {
                    if (x.name === "public_key") {
                        var pubKey = x.value.trim();
                        if (pubKey.startsWith("ssh-") && pubKey.includes(" ")) {
                            var parts = pubKey.split(" ", 2);
                            // eslint-disable-next-line dot-notation
                            acc["key_type"] = parts[0];
                            // eslint-disable-next-line dot-notation
                            acc["public_key"] = parts[1];
                        } else {
                            throw "Invalid Key format. Key should conform to openssh format \
                                   e.g.,\n\
                                   ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC/O... 'Key name' or\n\
                                   ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC/O...";
                        }
                    } else {
                        acc[x.name] = x.value;
                    }

                    return acc;
                }, {});

            $.ajax(
                "/api/v1/sftp_publickey/",
                {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": $.cookie("csrftoken"),
                        "Content-type": "application/json"
                    },
                    data: JSON.stringify(formData)
                }
            ).done(function(_json, _textStatus, _jqXHR) {
                $("#keyAddAlertMessage").empty();
                $("#keyAddAlert").hide();
                $("#keyAddModal").modal("hide");
                loadKeyTable(true);
            }).fail(function(jqXHR, _textStatus, err) {
                if (jqXHR.responseJSON !== "undefined") {
                    // eslint-disable-next-line dot-notation
                    err = jqXHR.responseJSON["sftp_publickey"]["__all__"][0];
                    $("#keyAddAlertMessage").text(err);
                    $("#keyAddAlert").show();
                } else {
                    err = "Encountered an unknown error. Please try again.";
                    $("#keyAddAlertMessage").text(err);
                }
            });
        } catch (e) {
            $("#keyAddAlertMessage").text(e);
            $("#keyAddAlert").show();
        }
    }

    function clearKeyAddForm() {
        $("#keyAddAlertMessage").empty();
        $("#keyAddAlert").hide();
        document.getElementById("keyAddForm").reset();
    }

    function clearKeyGenerateForm() {
        $("#keyGenerateAlertMessage").empty();
        $("#keyGenerateAlert").hide();
        document.getElementById("keyGenerateForm").reset();
    }

    /* eslint-disable object-shorthand */
    return {
        loadKeyTable: loadKeyTable,
        clearKeyAddForm: clearKeyAddForm,
        clearKeyGenerateForm: clearKeyGenerateForm,
        handleKeyDelete: handleKeyDelete,
        addKey: addKey
    };
    /* eslint-enable object-shorthand */
}());

$(document).on("submit", "#keyGenerateForm", function(e) {
    e.preventDefault();
    var url = $(this).prop("action");
    var method = $(this).prop("method");
    var form = $(this).serialize();

    $.ajax(
        url,
        {
            method: method, // eslint-disable-line object-shorthand
            headers: {
                "X-CSRFToken": $.cookie("csrftoken"),
            },
            data: form
        }
    ).done(function(data, textStatus, jqXHR) {
        if (textStatus === "success") {
            var blob = new Blob([data], {type: "application/octet-stream"});
            var disposition = jqXHR.getResponseHeader("content-disposition");
            var matches = /filename='(.+)'/.exec(disposition);
            var filename = (matches !== null && matches[1] ? matches[1] : "file");
            var objectURL = URL.createObjectURL(blob);
            var link = document.createElement("a");
            link.href = objectURL;
            link.download = filename;

            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(objectURL);

            $("#keyGenerateModal").modal("hide");
            sftp.clearKeyGenerateForm();
            sftp.loadKeyTable(true);
        }
    }).fail(function(jqXHR, _textStatus, _err) {
        $("#keyGenerateAlertMessage").text(jqXHR.responseJSON.error);
        $("#keyGenerateAlert").show();
    });
});

$(document).ready(function() {
    sftp.loadKeyTable(false);
});

