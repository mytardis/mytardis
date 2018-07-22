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
  <b>Delete<b></button></td></tr>"
}

function createKeyTable(keyData) {
  var table = $(document.createElement("table"))
    .addClass("table table-striped table-bordered")
    .attr("id", "keyTable")
    .append($("<thead><tr><th><h3>Key</h3></th></tr></thead>"));

  return keyData.reduce(function (acc, key) {
    return acc.append(addKeyRow(key))
  }, table)
}

function loadKeyTable(clear) {
  if (clear) {
    $("#keyTable").replaceWith(
      "<div id='keyTable'><p><img src=/static/images/ajax-loader-big.gif alt='loading...'/> Load keys...</p></div>"
    )
  }
  fetch(
    '/api/v1/sftp/key',
    {
      credentials: "include"
    }
  ).then(function(resp) {
    return resp.json();
  })
  .then(function(json) {
    var objs = json.objects
    if (objs.length > 0) {
      $("#keyTable").replaceWith(createKeyTable(objs))
    } else {
      $("#keyTable").replaceWith(createKeyAlert(
        "You don't have any public keys registered. Please add keys using the Add key button above.",
        "warning"
      ))
    }
  })
  .catch(function(err) {
    console.error("Error loading SSH keys:\n", err)
  })
}

function handleKeyDelete(keyId) {
  fetch(
    '/api/v1/sftp/key/' + keyId,
    {
      method: 'DELETE',
      credentials: 'include',
      headers: {
        'X-CSRFToken': $.cookie('csrftoken')
      }
    }
  ).then(function(resp) {
    $("#keyRow" + keyId).remove();
  }).catch(function(err) {
    console.error("SSH key delete error:\n", err);
  })
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

    fetch(
      '/api/v1/sftp/key/',
      {
        method: 'POST',
        credentials: 'include',
        headers: {
          'X-CSRFToken': $.cookie('csrftoken'),
          'Content-type': 'application/json'
        },
        body: JSON.stringify(form_data)
      }
    ).then(function(resp) {
      return resp.json()
    }).catch(function(err) {
      console.error("Error adding key:\n", err)
    }).then(function(json) {
      if (json !== undefined) {
        err = json['sftp/key']['__all__'][0]
        console.error("Key error: ", err)
        $("#keyAddAlertMessage").text(err)
        $("#keyAddAlert").show()
      } else {
        $("#keyAddAlertMessage").empty()
        $("#keyAddAlert").hide()
        $("#keyCreateModal").modal('hide');
        loadKeyTable(true)
      }
    })
  } catch (e) {
    $("#keyAddAlertMessage").text(e)
    $("#keyAddAlert").show()
  }
}

$(document).ready(function() {
  loadKeyTable(false)
})

function clearKeyAddForm() {
  $("#keyAddAlertMessage").empty()
  $("#keyAddAlert").hide()
  document.getElementById('keyAddForm').reset()
}
