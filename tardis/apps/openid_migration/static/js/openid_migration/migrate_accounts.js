/* tardis/apps/openid_migration/static/js/openid_migration/migrate_accounts.js */

var updateUserData = function(data) {
    $("#new_email").append("<td>" + data.data.new_user_email + "</td>");
    $("#old_username").append("<td>" + data.data.old_username + "</td>");
    $("#old_email").append("<td>" + data.data.old_user_email + "</td>");
    $("#new_username").append("<td>" + data.data.new_user_email + "</td>");
    // display Google or AAF image based on user current auth method
    var authMethod = data.data.auth_method;
    if (authMethod.toLowerCase() === "google") {
        $("#google_img").css("display", "block");
    } else if(authMethod.toLowerCase() === "aaf") {
        $("#aaf_img").css("display", "block");
    }

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
            window.location.replace("/");
        }
        else {
            $("#spinner").css("display", "none");
            $("#confirm-migrate").css("display", "none");
            $("#message").css("display", "none");
            $("#migration-failed-message").css("display", "block");
        }
    }, "json");
};

var cancelAccountMigration = function() {
    history.back();
};

$(document).ready(function() {
    $("#verify-my-account").on("click", verifyMyAccount);
    $("#confirm_true").on("click", migrateAccount);
    $("#confirm_false").on("click", cancelAccountMigration);
});
