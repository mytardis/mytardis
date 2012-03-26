var activateSearchAutocomplete = function() {
  var authMethod = "localdb";
  var data = { authMethod: authMethod };
  $.ajax({
    'global': false,
    'data': data,
    'url': '/ajax/parameter_field_list/',
    'success': function (data) {
        data = data.split("+");
        var list = _.map(data, function(line) {
            var name = line.split(":")[0];
            var type = line.split(":")[1];
            if (type == 'search_field')
                return name + ":";
            else
                return name;
        });
        $("#id_q").typeahead({
          'source': list,
          'items': 10
        });
    }
  });
};

var activateHoverDetection = function() {
  // Hover events
  $('.ui-state-default').live('mouseover mouseout', function(evt) {
    if (evt.type == 'mouseover') {
      $(this).addClass('ui-state-hover');
    } else {
      $(this).removeClass('ui-state-hover');
    }
  });
};

var userAutocompleteHandler = function(term, users, authMethod) {
  var matches = _(users).chain()
    // Filter out users which don't match auth method
    .filter(function(user) {
      // authMethods: ["testuser:localdb:Local DB"]
      return _(user.auth_methods).any(function(v) {
        return v.split(':')[1] == authMethod;
      })
    })
    // Filter out those that don't have a matching field
    .filter(function(user) {
      var fields = ['username', 'email', 'first_name', 'last_name'];
      // Select user if any of the fields above match
      return _(fields).any(function(fieldName) {
        var field = user[fieldName].toLowerCase();
        return _.str.include(field, term.toLowerCase());
      });
    })
    // Map to label/value objects
    .map(function(user) {
      var tmpl = "<%=first_name%> <%=last_name%> [<%=username%>] <<%=email%>>";
      // Create label and trim empty email
      var label = _.template(tmpl, user).replace(' <>','').trim();
      return { 'label': label, 'value': user.username };
    }).value();
  // Callback to autocomplete control
  return matches;
};

$(document).ready(function(){
  if ($('#id_q').length > 0) {
    activateSearchAutocomplete();
  }
  activateHoverDetection();
});
