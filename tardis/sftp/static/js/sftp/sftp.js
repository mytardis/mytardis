function handleKeyDelete(keyId, csrfToken) {
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
    if (resp.ok)
      $("#keyRow" + keyId).remove()
  })
}
