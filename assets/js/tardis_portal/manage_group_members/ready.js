/* manage_group_members/ready.js */

import {userAutocompleteHandler} from "../main";

var loadingHTML = "<img src=\"/static/images/ajax-loader.gif\"/>";

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
                            modal.modal("hide");
                        },
                        error: function(jqXHR, textStatus, errorThrown) {
                            modal.find("#error-message").html(jqXHR.responseText);
                            modal.find("#error-message").parents(".alert-danger").show();
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
        var usersuggest = form.find("[name=adduser]").val();
        var groupId = form.find("[name=group_id]").val();
        var usersDiv = form.parents(".access_list").children(".users");
        var isAdmin = form.find("[name=admin]").is(":checked");
        var action = "/group/" + groupId + "/add/" + usersuggest + "/?isAdmin=" + isAdmin + "&authMethod=" + authMethod;
        $.ajax({
            type: "GET",
            url: action,
            success: function(data) {
                usersDiv.hide().append(data).fadeIn();
            },
            error: function(data) {
                alert("Error adding user");
            }
        });
    });

    $(document).on("click", ".remove_user", function(evt) {
        evt.preventDefault();

        var accessList = $(this).parents(".access_list_user");

        $.ajax({
            "url": $(this).attr("href"),
            "success": function(data) {
                if (data === "OK") {
                    accessList.fadeOut(500);
                } else {
                    alert(data);
                }
            }
        });
    });
    //
    // // grouplist
    $("#grouplist").html(loadingHTML + "</br>");
    $("#grouplist").load("/ajax/group_list_by_user/");

    $(document).on("click", ".member_list_user_toggle", function(evt) {
        evt.preventDefault();

        var icon = $(this).find("i");
        icon.toggleClass("fa fa-folder-open");
        icon.toggleClass("fa fa-folder");
        $(this).toggleClass("members-shown members-hidden");

        var userList = $(this).parents(".group").find(".access_list");
        // If not showing members, just hide user list
        if (!$(this).hasClass("members-shown")) {
            userList.hide();
            return;
        }

        userList.html(loadingHTML);
        // Load (jQuery AJAX "load()") and show access list
        userList.load(this.href, function() {
            // Load user list and activate field autocompletion
            $.ajax({
                "dataType": "json",
                "url": "/ajax/user_list/",
                "success": function(users) {
                    var autocompleteHandler = function(usersForHandler, query, callback) {
                        return callback(userAutocompleteHandler(query, usersForHandler));
                    };
                    $("#id_adduser").typeahead({
                        "source": autocompleteHandler.bind(this, users),
                        "displayText": function(item) {
                            return item.label;
                        },
                        "updater": function(item) {
                            return item.value;
                        }
                    });
                }
            });
        }).show();
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

