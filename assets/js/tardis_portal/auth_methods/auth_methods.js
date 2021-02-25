/* auth_methods.js */
/* global authMethodDict */

var showChangePasswordForm = 0;

var displayError = function(msg, elem) {
    // Create box from template
    var msgBox = $("#template-block .alert-error-msg").clone();
    // Fill in error message
    msgBox.find(".msg").text(msg);
    // Insert into DOM
    msgBox.insertBefore(elem).fadeIn("slow").animate({opacity: 1.0}, 5000).fadeOut(
        "slow", function() {
            msgBox.remove();
        });
};

var removeAuth = function(event) {
    if (confirm("Are you sure you want to delete this authentication method?")) {
        var divId = this.id;
        var authDesc = $(this).data("auth-desc");
        var authData = {
            operation: "removeAuth", authMethod: divId,
            csrfmiddlewaretoken: $("#csrf-token").val() };
        $.post("/accounts/manage_auth_methods/", authData, function(data) {
            if (data.status === "success") {
                $("div").remove("#authMethod_" + divId);
                $(`<option value="${divId}">${authDesc}</option>`).insertAfter($("option:last"));
            }
            else {
                displayError(data.errorMessage, $("div #authMethod_" + divId));
            }
        }, "json");
    }
};

var editAuth = function(event) {
    var divId = this.id;
    if (showChangePasswordForm === 0) {
        var changePassword = $("#template-block .form-change-password").clone();
        showChangePasswordForm = 1;
        changePassword.appendTo("#authMethod_" + divId);
        $("#" + divId + ".edit_auth username-edit-icon").css("display", "none");
        $("#" + divId + ".edit_auth username-close-icon").css("display", "inline");
    }
    else {
        showChangePasswordForm = 0;
        $("#authMethod_" + divId).find(".form-change-password").remove();
        $("#" + divId + ".edit_auth username-close-icon").css("display", "none");
        $("#" + divId + ".edit_auth username-edit-icon").css("display", "inline");
    }
};

var processNewAuthEntry = function(data) {
    var dataMap = data.data;
    var username = dataMap.username;
    var authenticationMethod = dataMap.authenticationMethod;

    var newAuthMethod = $("#template-block .authMethod").clone();
    newAuthMethod.attr("id", "authMethod_" + authenticationMethod);
    newAuthMethod.find(".remove_auth").attr("id", authenticationMethod);
    newAuthMethod.find(".username").text(username);
    newAuthMethod.find(".auth-method").text(authMethodDict[authenticationMethod]);
    newAuthMethod.insertAfter($(".authMethod:visible:last"));

    var supportedAuthMethodsLength = dataMap.supportedAuthMethodsLen;
    if (supportedAuthMethodsLength === 0) {
        $("div").remove("#authForm");
    }
    else {
        $("option").remove(`option[value="${authenticationMethod}"]`);
        $("#id_username").val("");
        $("#id_password").val("");
    }
};

// eslint-disable-next-line complexity
var editAccount = function() {
    var currentPassword = $("#id_currentPassword").val();
    var password = $("#id_newPassword").val();
    var password1 = $("#id_newPassword1").val();

    if (currentPassword === "" || password === "" || password1 === "") {
        displayError("Sorry, all the password fields should be filled.", $("div.authMethod .form-change-password"));
    }
    else if (password !== password1) {
        displayError("The passwords don't match.", $("div.authMethod .form-change-password"));
    }
    else {
        var authData = {
            operation: "editAuth", currentPassword: currentPassword, newPassword: password,
            csrfmiddlewaretoken: $("#csrf-token").val() };
        $.post("/accounts/manage_auth_methods/", authData, function(data) {
            if (data.status === "success") {
                showChangePasswordForm = 0;
                $("div.authMethod").find(".form-change-password").remove();
                $("div.edit_auth username-close-icon").css("display", "none");
                $("div.edit_auth username-edit-icon").css("display", "inline");
                var msgDiv = $("#template-block .alert-password-changed").clone();
                msgDiv.appendTo(".authMethod").fadeIn("slow").animate({opacity: 1.0}, 5000).fadeOut(
                    "slow", function() {
                        msgDiv.remove();
                    });
            }
            else {
                displayError(data.errorMessage, $("div.authMethod .form-change-password"));
            }
        }, "json");
    }
    return false;
};

var linkAccount = function() {
    var username = $("#id_username").val();
    var password = $("#id_password").val();
    var authenticationMethod = $("#id_authenticationMethod").val();

    if (username !== "" && password !== "" && authenticationMethod !== "") {
        var authData = {
            operation: "addAuth", username: username, password: password, authenticationMethod: authenticationMethod,
            csrfmiddlewaretoken: $("#csrf-token").val()
        };
        $.post("/accounts/manage_auth_methods/", authData, function(data) {
            if (data.status === "success") {
                processNewAuthEntry(data);
            }
            else if (data.status === "confirm") {
                var confirmMessage = "This process would involve merging the two accounts you own.\nWould you like to continue?";
                if (confirm(confirmMessage)) {
                    authData = {
                        operation: "mergeAuth", username: username, password: password, authenticationMethod: authenticationMethod,
                        csrfmiddlewaretoken: $("#csrf-token").val()
                    };
                    $.post("/accounts/manage_auth_methods/", authData, function(data2) {
                        if (data2.status === "success") {
                            processNewAuthEntry(data2);
                        }
                        else {
                            displayError("Account merging failed!", $("#authForm"));
                        }
                    }, "json");
                }
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

$("#link").click(linkAccount);
$(document).on("click", "#edit", editAccount);
$(document).on("click", ".edit_auth", editAuth);
$(document).on("click", ".remove_auth", removeAuth);
