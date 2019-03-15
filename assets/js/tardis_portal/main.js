/* global $, _, s */
/* eslint strict: 0 */

// eslint-disable-next-line no-unused-vars
export function userAutocompleteHandler(term, users, authMethod) {
    var matches = _(users).chain()
    // Filter out users which don"t match auth method
    /** .filter(function(user) {
            // authMethods: ["testuser:localdb:Local DB"]
            return _(user.auth_methods).any(function(v) {
                return v.split(":")[1] === authMethod;
            });
        })
     **/

        // Filter out those that don"t have a matching field
        .filter(function(user) {
            var fields = ["username", "email", "first_name", "last_name"];
            // Select user if any of the fields above match
            return _(fields).any(function(fieldName) {
                var field = user[fieldName].toLowerCase();
                return s.include(field, term.toLowerCase());
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
}

// eslint-disable-next-line no-unused-vars

