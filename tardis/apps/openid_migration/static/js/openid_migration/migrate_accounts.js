/* tardis/apps/openid_migration/static/js/openid_migration/migrate_accounts.js */

/* eslint global-strict: 0, strict: 0, object-shorthand: 0 */

var updateUserData = function(data) {
    $("#current_user_email").append(data.data.new_user_email);
    $("#old_username").append("<td>" + data.data.old_username + "</td>");
    $("#old_email").append("<td>" + data.data.old_user_email + "</td>");
};

var displayError = function(msg, elem) {
    // Create box from template
    var msgBox = $("#template-block .alert-error-msg").clone();
    // Fill in error message
    msgBox.find(".msg").text(msg);
    // Insert into DOM
    msgBox.insertBefore(elem).fadeIn("slow").animate({opacity: 1.0}, 5000).fadeOut("slow", function() { msgBox.remove(); });
};

var verifyMyAccount = function() {
    var username = $("#id_username").val();
    var password = $("#id_password").val();
    var authenticationMethod = $("#id_authenticationMethod").val();

    if (username !== "" && password !== "") {
        var postData = {operation: "addAuth", username: username, password: password, authenticationMethod: authenticationMethod,
            csrfmiddlewaretoken: $("#csrf-token").val()
        };
        $.post("/apps/openid-migration/migrate-accounts/", postData, function(data) {
            var status = data.status;
            if (status === "confirm") {
                $("#authForm").css("display", "none");
                $(".alert-info").css("display", "none");
                $("#confirm-migrate").css("display", "block");
                updateUserData(data);
            } else {
                displayError(data.errorMessage, $("#authForm"));
            }
        }, "json");
    }
    else {
        displayError("You need to provide all the necessary information to authenticate.", $("#authForm"));
    }
    return false;
};

var migrateAccount = function() {
    $("#spinner").css("display", "block");
    $("#confirm-migrate").css("opacity", ".5");
    var username = $("#id_username").val();
    var password = $("#id_password").val();
    var authenticationMethod = $("#id_authenticationMethod").val();
    var postData = {
        operation: "migrateAccount", username: username, password: password, authenticationMethod: authenticationMethod,
        csrfmiddlewaretoken: $("#csrf-token").val()
    };
    $.post("/apps/openid-migration/migrate-accounts/", postData, function(data) {
        var status = data.status;
        if (status === "success") {
            $("#spinner").css("display", "none");
            $("#confirm-migrate").css("display", "none");
            $("#message").css("display", "none");
            $("#migration-success-message").css("display", "block");
            $("#migration-success-message span span").text(data.data.auth_method);
        }
        else {
            $("#spinner").css("display", "none");
            $("#confirm-migrate").css("display", "none");
            $("#message").css("display", "none");
            $("#migration-failed-message").css("display", "block");
        }
    }, "json");
};

$(document).ready(function() {
    $("#verify-my-account").on("click", verifyMyAccount);
    $("#confirm_true").on("click", migrateAccount);
});
