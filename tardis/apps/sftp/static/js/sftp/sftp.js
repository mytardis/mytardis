function createKeyAlert(msg, level) {
  return "<div id='keyTable' class='alert alert-block alert-" + level + "'>\
  <span class='message'>" + msg + "</span> \
  </div>";
}

function addKeyRow(rowData) {
  return "<tr id='keyRow" + rowData.id + "'>\
  <td><div class='pull-left'><h3 style='margin-left:12px 0;'>" + rowData.name + "</h3>\
  <p style='margin: 9px 0'>Type: " + rowData.key_type.toUpperCase() + "<p>\
  <p>Fingerprint: " + rowData.fingerprint + "</p>\
  <p>Date added: " + rowData.added + "</p></div>\
  <button id='delete-btn' class='btn pull-right' \
  onclick='handleKeyDelete(" + rowData.id + ")'>\
  <b>Delete<b></button></td></tr>";
}

function createKeyTable(keyData) {
  var table = $(document.createElement("table"))
    .addClass("table table-striped table-bordered")
    .attr("id", "keyTable")
    .append($("<thead><tr><th><h3>Key</h3></th></tr></thead>"));

  return keyData.reduce(function (acc, key) {
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
    '/api/v1/sftp/key'
  ).done(function(json, textStatus, jqXHR) {
    var objs = json.objects
    if (objs.length > 0) {
      $("#keyTable").replaceWith(createKeyTable(objs));
    } else {
      $("#keyTable").replaceWith(createKeyAlert(
        "You don't have any public keys registered. Please add keys using the Add key button above.",
        "warning"
      ));
    }
  })
  .fail(function(jqXHR, textStatus, err) {
    console.error("Error loading SSH keys:\n", err)
  });
}

function handleKeyDelete(keyId) {
  $.ajax(
    '/api/v1/sftp/key/' + keyId,
    {
      method: 'DELETE',
      headers: {
        'X-CSRFToken': $.cookie('csrftoken')
      }
    }
  ).done(function(data, textStatus, jgXHR) {
    // $("#keyRow" + keyId).remove();
    loadKeyTable(true);
  }).fail(function(jqXHR, textStatus, err) {
    console.error("SSH key delete error:\n", err);
  });
}

function addKey() {
  try {
    form_data = $("#keyAddForm")
      .serializeArray()
      .reduce(function(acc, x) {
        if (x['name'] === 'public_key') {
          pub_key = x['value'].trim()
          if (pub_key.startsWith("ssh-") && pub_key.includes(" ")) {
            parts = pub_key.split(' ', 2)
            acc['key_type'] = parts[0]
            acc['public_key'] = parts[1]
          } else {
            throw "Invalid Key format. Key should conform to openssh format \
                   e.g.,\n\
                   ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC/O... 'Key name' or\n\
                   ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC/O..."
          }
        } else {
          acc[x['name']] = x['value'];
        }

        return acc
      }, {});

    $.ajax(
      '/api/v1/sftp/key/',
      {
        method: 'POST',
        headers: {
          'X-CSRFToken': $.cookie('csrftoken'),
          'Content-type': 'application/json'
        },
        data: JSON.stringify(form_data)
      }
    ).done(function(json, textStatus, jqXHR) {
      $("#keyAddAlertMessage").empty();
      $("#keyAddAlert").hide();
      $("#keyAddModal").modal('hide');
      loadKeyTable(true)
    }).fail(function(jqXHR, textStatus, err) {
      if (jqXHR.responseJSON !== "undefined") {
        err = jqXHR.responseJSON['sftp/key']['__all__'][0]
        console.error("Key error: ", err)
        $("#keyAddAlertMessage").text(err);
        $("#keyAddAlert").show();
      } else {
        console.error(err);
      }
    })
  } catch (e) {
    $("#keyAddAlertMessage").text(e)
    $("#keyAddAlert").show()
  }
}

function clearKeyAddForm() {
  $("#keyAddAlertMessage").empty();
  $("#keyAddAlert").hide();
  document.getElementById('keyAddForm').reset();
}

$(document).on("submit", "#keyGenerateForm", function(e) {
  e.preventDefault();
  var url = $(this).prop('action');
  var method = $(this).prop('method');
  var form = $(this).serialize();

  $.ajax(
    url,
    {
      method: method,
      headers: {
        'X-CSRFToken': $.cookie('csrftoken'),
      },
      data: form
    }
  ).done(function(data, textStatus, jqXHR) {
    if (textStatus === "success") {
      var blob = new Blob([data], {type: 'application/octet-stream'})
      var disposition = jqXHR.getResponseHeader('content-disposition');
      var matches = /filename='(.+)'/.exec(disposition);
      var filename = (matches !== null && matches[1]? matches[1] : 'file');
      var objectURL = URL.createObjectURL(blob);
      var link = document.createElement('a');
      link.href = objectURL;
      link.download = filename;

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(objectURL);

      $("#keyGenerateModal").modal("hide");
      loadKeyTable(true);
    }
  }).fail(function(jqXHR, textStatus, err) {
    console.error(err);
    $("#keyGenerateAlertMessage").text(jqXHR.responseJSON['error']);
    $("#keyGenerateAlert").show();
  });
})

$(document).ready(function() {
  loadKeyTable(false);
})

