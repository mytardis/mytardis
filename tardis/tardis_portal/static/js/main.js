/* global $ */
/* global _ */
/* eslint global-strict: 0, strict: 0, object-shorthand: 0 */
var activateSearchAutocomplete = function() {
    var authMethod = "localdb";
    var authMethodDict = { authMethod: authMethod };
    $.ajax({
        "global": false,
        "data": authMethodDict,
        "url": "/search/parameter_field_list/",
        "success": function(data) {
            data = data.split("+");
            var list = _.map(data, function(line) {
                var name = line.split(":")[0];
                var type = line.split(":")[1];
                if (type === "search_field") {
                    return name + ":";
                }
                else {
                    return name;
                }
            });
            $("#id_q").typeahead({
                "source": list,
                "items": 10
            });
        }
    });
};

var activateHoverDetection = function() {
    // Hover events
    $(document).on("mouseover mouseout", ".ui-state-default", function(evt) {
        if (evt.type === "mouseover") {
            $(this).addClass("ui-state-hover");
        } else {
            $(this).removeClass("ui-state-hover");
        }
    });
};

// eslint-disable-next-line no-unused-vars
var userAutocompleteHandler = function(term, users, authMethod) {
    var matches = _(users).chain()
        // Filter out users which don"t match auth method
        .filter(function(user) {
            // authMethods: ["testuser:localdb:Local DB"]
            return _(user.auth_methods).any(function(v) {
                return v.split(":")[1] === authMethod;
            });
        })
        // Filter out those that don"t have a matching field
        .filter(function(user) {
            var fields = ["username", "email", "first_name", "last_name"];
            // Select user if any of the fields above match
            return _(fields).any(function(fieldName) {
                var field = user[fieldName].toLowerCase();
                return _.str.include(field, term.toLowerCase());
            });
        })
        // Map to label/value objects
        .map(function(user) {
            var tmpl = _.template("<%=firstName%> <%=lastName%> [<%=username%>] <<%=email%>>");
            // Create label and trim empty email
            var label = tmpl({
                firstName: user.first_name,
                lastName: user.last_name,
                username: user.username,
                email: user.email}).replace(" <>", "").trim();
            return { "label": label, "value": user.username };
        }).value();
    // Callback to autocomplete control
    return matches;
};

// eslint-disable-next-line no-unused-vars
var isLoggedIn = function() {
    return $("#user-menu").length > 0;
};

$(document).ready(function() {
    if ($("#id_q").length > 0) {
        activateSearchAutocomplete();
    }
    activateHoverDetection();
});
