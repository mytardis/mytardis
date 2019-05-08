/* global _, s */

export function userAutocompleteHandler(term, users) {
    var matches = _(users).chain()
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
