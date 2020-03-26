/* manage_group_members/ready.js */

import {userAutocompleteHandler} from "../main";

var loadingHTML = "<img src=\"/static/images/ajax-loader.gif\"/>";

function loadUserListForGroup($userList, url, groupId) {
    // Remove any existing add-user form before showing a new one:
    $(".add-user-form").remove();

    $userList.html(loadingHTML);
    // Load (jQuery AJAX "load()") and show access list
    $userList.load(url, function() {
        // Load user list and activate field autocompletion
        $.ajax({
            "dataType": "json",
            "url": "/ajax/user_list/",
            "success": function(users) {
                var autocompleteHandler = function(usersForHandler, query, callback) {
                    return callback(userAutocompleteHandler(query, usersForHandler));
                };
                $("#id_adduser-" + groupId).typeahead({
                    "source": autocompleteHandler.bind(this, users),
                    "displayText": function(item) {
                        return item.label;
                    },
                    "updater": function(item) {
                        return item.value;
                    }
                });
                $("#id_adduser-" + groupId).on("keydown", function() {
                    /* Validation is server-side.
                     * When user starts typing in an input to correct a validation
                     * error, the invalid status should be removed. */
                    $(this).removeClass("is-invalid");
                    $(this)[0].setCustomValidity("");
                    $(".add-user-form").removeClass("was-validated");
                });
                /**
                 * Used to hide an alert instead of it removing it
                 * which is the default action of when using
                 * Bootstrap's data-dismiss attribute.
                 */
                $("[data-hide]").on("click", function() {
                    $(this).closest("." + $(this).data("hide")).hide();
                });
            }
        });
    }).show();
}

$(document).ready(function() {

    $(document).on("click", ".create_group_link", function(evt) {
        var modal = $("#modal-create-group");

        modal.find(".modal-body").html("");
        modal.find(".loading-placeholder").show();
        modal.modal("show");

        modal.find(".modal-body")
            .load("/experiment/control_panel/create/group/", function() {
                modal.find(".loading-placeholder").hide();
                modal.find("#error-message").parents(".alert-danger").hide();

                $("#id_addgroup").on("keydown", function() {
                    /* Validation is server-side.
                     * When user starts typing in an input to correct a validation
                     * error, the invalid status should be removed. */
                    $(this).removeClass("is-invalid");
                    $(this)[0].setCustomValidity("");
                    $("#create-group-form").removeClass("was-validated");
                });

                $("#id_groupadmin").on("keydown", function() {
                    /* Validation is server-side.
                     * When user starts typing in an input to correct a validation
                     * error, the invalid status should be removed. */
                    $(this).removeClass("is-invalid");
                    $(this)[0].setCustomValidity("");
                    $("#create-group-form").removeClass("was-validated");
                });

                $("#group.form_submit").unbind("click");
                $("#group.form_submit").on("click", function(event) {
                    event.preventDefault();

                    var group = $(this).parents(".group_create").find("#id_addgroup").val();
                    var admin = $(this).parents(".group_create").find("#id_groupadmin").val();

                    var getVars = "?group=" + group + "&admin=" + admin;
                    var action = "/experiment/control_panel/create/group/" + getVars;

                    $.ajax({
                        "global": true,
                        type: "GET",
                        url: action,
                        dataType: "text",
                        success: function(data) {
                            $("#create-group-form").addClass("was-validated");
                            modal.modal("hide");
                        },
                        error: function(jqXHR, textStatus, errorThrown) {
                            var response = JSON.parse(jqXHR.responseText);
                            if (response && "field" in response && response.field) {
                                var inputElement = $("#" + response.field);
                                inputElement.addClass("is-invalid");

                                // Without this line, a tick might be displayed implying that
                                // the input is valid, even when it has the "is-invalid" class:
                                inputElement[0].setCustomValidity(response.message);

                                var feedbackElement = inputElement.siblings(".invalid-feedback");
                                feedbackElement.html(response.message);

                                $("#create-group-form").addClass("was-validated");
                            }
                            else if (response) {
                                modal.find("#error-message").html(jqXHR.response.message);
                                modal.find("#error-message").parents(".alert-danger").show();
                            }
                            else {
                                modal.find("#error-message").html(jqXHR.responseText);
                                modal.find("#error-message").parents(".alert-danger").show();
                            }
                        }
                    });
                    return false;
                });

            });

    });

    $("#modal-create-group").bind("hidden.bs.modal", function() {
        var $targetGroupList = $("#grouplist");
        $targetGroupList.html(loadingHTML + "</br>");
        var href = "/ajax/group_list_by_user/";
        $targetGroupList.load(href);
    });


    $(document).on("submit", "form.add-user-form", function(evt) {
        evt.preventDefault();
        var form = $(this);
        var authMethod = form.find("[name=authMethod]").val();
        var username = form.find("[name=adduser]").val();
        var groupId = form.find("[name=group_id]").val();
        var usersDiv = form.parents(".access_list").children(".users");
        var isAdmin = form.find("[name=admin]").is(":checked");
        var action = "/group/" + groupId + "/add/" + username + "/?isAdmin=" + isAdmin + "&authMethod=" + authMethod;

        if (!username) {
            var userInput = form.find("[name=adduser]");
            var feedbackElement = userInput.siblings(".invalid-feedback");
            userInput.addClass("is-invalid");

            var msg = "User cannot be blank";
            // Without this line, a tick might be displayed implying that
            // the input is valid, even when it has the "is-invalid" class:
            userInput[0].setCustomValidity(msg);

            feedbackElement.html(msg);
            form.addClass("was-validated");
            return false;
        }

        $.ajax({
            type: "GET",
            url: action,
            success: function(data) {
                usersDiv.hide().append(data).fadeIn();
            },
            error: function(jqXHR, textStatus, errorThrown) {
                var response = JSON.parse(jqXHR.responseText);
                if (response && "field" in response && response.field) {
                    var inputElement = $("#" + response.field);
                    inputElement.addClass("is-invalid");

                    // Without this line, a tick might be displayed implying that
                    // the input is valid, even when it has the "is-invalid" class:
                    inputElement[0].setCustomValidity(response.message);

                    var invalidFeedbackElement = inputElement.siblings(".invalid-feedback");
                    invalidFeedbackElement.html(response.message);

                    form.addClass("was-validated");
                }
            }
        });
    });

    $(document).on("click", ".remove_user", function(evt) {
        evt.preventDefault();

        var accessListUser = $(this).parents(".access_list_user");
        var accessList = $(this).parents(".access_list");
        var addUserForm = accessList.find(".add-user-form");
        var removeUserButton = $(this);

        $.ajax({
            "url": $(this).attr("href"),
            "success": function(data) {
                accessListUser.fadeOut(500);
            },
            "error": function(jqXHR, textStatus, errorThrown) {
                removeUserButton.parents(".users").find(".alert").show();
            },
            "complete": function(jqXHR, textStatus, errorThrown) {
                var inputElement = accessList.find("[name=adduser]");
                inputElement.removeClass("is-invalid");
                inputElement[0].setCustomValidity("");
                addUserForm.removeClass("was-validated");
            }

        });
    });
    //
    // // grouplist
    $("#grouplist").html(loadingHTML + "</br>");
    $("#grouplist").load("/ajax/group_list_by_user/");

    $(document).on("click", "a.member_list_user_toggle", function(evt) {
        evt.preventDefault();

        var groupId = $(this).data("group_id");
        var $icon = $(this).siblings("a").find("i.group-icon");
        $icon.toggleClass("fa-folder fa-folder-open");
        $(this).toggleClass("members-shown members-hidden");

        var $userList = $(this).parents(".group").find(".access_list");
        // If not showing members, just hide user list
        if (!$(this).hasClass("members-shown")) {
            $userList.hide();
            return;
        }

        loadUserListForGroup($userList, this.href, groupId);
    });

    $(document).on("click", "a i.group-icon", function(evt) {
        evt.preventDefault();

        var $groupLink = $(this).parent().siblings("a.member_list_user_toggle");
        var groupId = $groupLink.data("group_id");
        $(this).toggleClass("fa-folder fa-folder-open");
        $groupLink.toggleClass("members-shown members-hidden");

        var $userList = $groupLink.parents(".group").find(".access_list");
        // If not showing members, just hide user list
        if (!$groupLink.hasClass("members-shown")) {
            $userList.hide();
            return;
        }

        loadUserListForGroup($userList, $groupLink.attr("href"), groupId);
    });

    // add user
    $(document).on("click", ".create_user_link", function(evt) {
        var modal = $("#modal-create-user");

        modal.find(".modal-body").html("");
        modal.find(".loading-placeholder").show();
        modal.modal("show");

        modal.find(".modal-body")
            .load("/experiment/control_panel/create/user/", function() {
                modal.find(".loading-placeholder").hide();

                $("#user.form_submit").unbind("click");
                $("#user.form_submit").on("click", function(event) {
                    event.preventDefault();

                    var username = $(this).parents(".user_create").find("#id_username").val();
                    var email = $(this).parents(".user_create").find("#id_email").val();
                    var password1 = $(this).parents(".user_create").find("#id_password1").val();
                    var password2 = $(this).parents(".user_create").find("#id_password2").val();
                    var authMethod = $(this).parents(".user_create").find("#id_authMethod").val();

                    var postVars = {
                        user: username,
                        email: email,
                        authMethod: authMethod,
                        password: password1,
                        csrfmiddlewaretoken: $("#csrf-token").val()
                    };
                    var action = "/experiment/control_panel/create/user/";

                    // returns 0 on fail
                    var passwordMatch = password1.localeCompare(password2);

                    if (!passwordMatch)
                    {

                        $.ajax({
                            "global": true,
                            type: "POST",
                            url: action,
                            data: postVars,
                            success: function(data) {
                                $("#success-message").html(data);
                                $("#success-message").parents(".alert-success").attr("style", "display: block;");
                                modal.modal("hide");
                            },
                            error: function(data) { alert(data.responseText || "An error has occurred"); }
                        });
                        return false;
  
                    }
                    else
                    {
                        alert("Passwords do not match!");
                    }

                }); // end form submit event

            });

    });

    $("#modal-create-group").bind("hidden.bs.modal", function() {
        var $targetGroupList = $("#grouplist");
        $targetGroupList.html(loadingHTML + "</br>");
        var href = "/ajax/group_list_by_user/";
        $targetGroupList.load(href);
    });


});

