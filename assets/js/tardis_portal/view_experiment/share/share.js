/* jQuery code for experiment view's Sharing tab */

import { userAutocompleteHandler } from "../../main";

import { loadExpTabPane } from "../experiment-tabs.js";
var loadingHTML = "<img src=\"/static/images/ajax-loader.gif\"/><br />";

// beginswith, endswith
String.prototype.beginsWith = function(t, i) {
    if (i === false) {
        return (t === this.substring(0, t.length));
    } else {
        return (t.toLowerCase() === this.substring(0, t.length).toLowerCase());
    }
};

String.prototype.endsWith = function(t, i) {
    if (i === false) {
        return (t === this.substring(this.length - t.length));
    } else {
        return (t.toLowerCase() === this.substring(this.length - t.length).toLowerCase());
    }
};

// user sharing modal

const userSharingModalLoaded = function() {
    var modal = $("#modal-share");
    modal.find(".loading-placeholder").hide();

    $("#id_entered_user").keypress(function(e) {
        // Reset autocomplete user when typing in the user edit field.
        $(this).siblings("#id_autocomp_user").val("");
        $(this).siblings("#id_authMethod").attr("disabled", "");

        if (e.keyCode === 13)
        {
            $("#user.form_submit").click();
        }
    });
    // Load user list and activate field autocompletion
    $.ajax({
        dataType: "json",
        url: "/ajax/user_list/",
        success: function(users) {
            if($("select#id_authMethod option").length === 1) {
                $("#id_authMethod_label").hide();
                $("#id_authMethod").hide();
            }
            var autocompleteHandler = function(usersForHandler, query, callback) {
                return callback(userAutocompleteHandler(query, usersForHandler));
            };
            $("#id_entered_user").typeahead({
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


    $("#user.form_submit").unbind("click");
    // eslint-disable-next-line complexity
    $("#user.form_submit").click(function(event) {
        event.preventDefault();
        var enteredUser = $(this).siblings("#id_entered_user").val();
        var autocompUser = $(this).siblings("#id_autocomp_user").val();
        var username = null;
        var authMethod = null;
        if (autocompUser !== "") {
            // Use the details from the autocomplete.
            autocompUser = autocompUser.split(":");
            username = autocompUser[0];
            authMethod = autocompUser[1];
        } else {
            // Autocomplete failed. Use the entered username as-is.
            username = enteredUser;
            authMethod = $(this).siblings("#id_authMethod").val();
        }
        var usersDiv = $(this).parents(".access_list1").children(".users");
        var userMessagesDiv = $("#user-sharing-messages");
        var permissions = $(this).siblings("#id_permission").val();

        var canRead = false;
        var canDownload = false;
        var canWrite = false;
        var isOwner = false;
        var canSensitive = false;
        var canDelete = false;
        if (permissions === "read") {
            canRead = true;
        }
        else if (permissions === "download") {
            canRead = true;
            canDownload = true;
        }
        else if(permissions === "sensitive") {
            canRead = true;
            canDownload = true;
            canSensitive = true;
        }
        else if (permissions === "edit") {
            canRead = true;
            canDownload = true;
            canSensitive = true;
            canWrite = true;
        }
        else if (permissions === "owner") {
            canRead = true;
            canDownload = true;
            canWrite = true;
            isOwner = true;
            canSensitive = true;
            canDelete = true;
        }

        permissions = "/?authMethod=" + authMethod + "&canRead=" + canRead +
                      "&canDownload=" + canDownload + "&canWrite=" + canWrite +
                      "&canDelete=" + canDelete + "&canSensitive=" + canSensitive +
                      "&isOwner=" + isOwner;
        var action = "/experiment/control_panel/" + $("#experiment-id").val() +
            "/access_list/add/user/" + username + permissions;

        $.ajax({
            type: "GET",
            url: action,
            success: function(data) {
                usersDiv.hide().append(data).fadeIn();
                userMessagesDiv.hide().html("");
                // todo this is a duplicate function..
                $(".remove_user").unbind("click");
                $(".remove_user").click(function() {
                    var href = $(this).attr("href");
                    var removeUser = $(this);
                    $.ajax({
                        global: false,
                        url: href,
                        success: function() {
                            removeUser.fadeOut(300, function() {
                                removeUser.parents(".access_list_user").remove();
                            });
                        },
                        error: function(jqXHR, textStatus, errorThrown) {
                            alert(jqXHR.responseText);
                        },
                        complete: function() {
                            userMessagesDiv.hide().html("");
                        }
                    }); // end ajax
                    return false;
                }); // end remove user
            },
            error: function(jqXHR, textStatus, errorThrown) {
                if (jqXHR.status === 400) {
                    userMessagesDiv.hide().html(jqXHR.responseText).fadeIn();
                    return;
                }
                userMessagesDiv.hide().html("");
                alert("Error adding user");
            }
        });
        return false;
    });

    $(".remove_user").unbind("click");
    $(".remove_user").click(function() {
        var href = $(this).attr("href");
        var removeUser = $(this);
        $.ajax({
            global: false,
            url: href,
            success: function() {
                removeUser.fadeOut(300, function() {
                    removeUser.parents(".access_list_user").remove();
                });
            },
            error: function(jqXHR, textStatus, errorThrown) {
                alert(jqXHR.responseText);
            },
            complete: function() {
                $("#user-sharing-messages").hide().html("");
            }
        }); // end ajax
        return false;
    }); // end remove user
};

export function addUserSharingEventHandlers() {
    $(".share_link").unbind("click");
    $(".share_link").bind("click", function(evt) {
        var modal = $("#modal-share");

        modal.find(".modal-body").html("");
        modal.find(".loading-placeholder").show();
        modal.modal("show");

        var userSharingModalContentUrl = "/experiment/control_panel/" +
                                         $("#experiment-id").val() +
                                         "/access_list/user/";
        modal.find(".modal-body")
            .load(userSharingModalContentUrl, userSharingModalLoaded);
    });

    $("#modal-share").bind("hidden.bs.modal", function() {
        loadExpTabPane("sharing");
    });
}

// group sharing modal

const groupSharingModalLoaded = function() {
    var modal = $("#modal-share-group");
    modal.find(".loading-placeholder").hide();

    $.ajax({
        global: false,
        url: "/ajax/group_list/",
        success: function(data) {
            var groups = data;
            $(".groupsuggest").typeahead({
                "source": groups.split(" ~ ")
            });
        }
    });

    $("#id_addgroup").keypress(function(e) {
        if (e.keyCode === 13)
        {
            $("#group.form_submit").click();
        }
    });


    // view group members
    $(".member_list_user_toggle").unbind("click");
    $(".member_list_user_toggle").bind("click", function(evt2) {
        evt2.preventDefault();

        var icon = $(this).find("i");
        icon.toggleClass("fa-folder fa-folder-open");
        $(this).toggleClass("members-shown members-hidden");

        var userList = $(this).parents(".access_list_group").find(".access_list");
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
                dataType: "json",
                url: "/ajax/user_list/",
                success: function(users2) {
                    var autocompleteHandler = function(usersForHandler, query, callback) {
                        return callback(userAutocompleteHandler(query, usersForHandler));
                    };
                    $("#id_adduser").typeahead({
                        "source": autocompleteHandler.bind(this, users2),
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

    $("#group.form_submit").unbind("click");
    $("#group.form_submit").click(function(event) {
        event.preventDefault();

        var groupsuggest = $(this).parents(".access_list2").find(".groupsuggest").val();
        var groupsDiv = $(this).parents(".access_list2").children(".groups");
        var groupMessagesDiv = $("#group-sharing-messages");

        var action = "/experiment/control_panel/" + $("#experiment-id").val() + "/access_list/add/group/" + groupsuggest;

        var permissions = $("#id_permission_group").val();

        var canRead = false;
        var canDownload = false;
        var canWrite = false;
        var isOwner = false;
        var canSensitive = false;
        var canDelete = false;
        if(permissions === "read") {
            canRead = true;
        }
        else if(permissions === "download") {
            canRead = true;
            canDownload = true;
        }
        else if(permissions === "sensitive") {
            canRead = true;
            canDownload = true;
            canSensitive = true;
        }
        else if(permissions === "edit") {
            canRead = true;
            canDownload = true;
            canSensitive = true;
            canWrite = true;
        }
        else if(permissions === "owner") {
            canRead = true;
            canDownload = true;
            canWrite = true;
            isOwner = true;
            canSensitive = true;
            canDelete = true;
        }

        permissions = "/?canRead=" + canRead + "&canDownload=" + canDownload +
                      "&canWrite=" + canWrite + "&canDelete=" + canDelete +
                      "&canSensitive=" + canSensitive + "&isOwner=" + isOwner;
        action = action + permissions;

        $.ajax({
            "global": true,
            type: "GET",
            url: action,
            success: function(data) {
                groupsDiv.hide().append(data).fadeIn();
                groupMessagesDiv.hide().html("");

                // view group members
                $(".member_list_user_toggle").unbind("click");
                $(".member_list_user_toggle").bind("click", function(evt2) {
                    evt2.preventDefault();

                    var icon = $(this).find("i");
                    icon.toggleClass("fa-folder fa-folder-open");
                    $(this).toggleClass("members-shown members-hidden");

                    var userList = $(this).parents(".access_list_group").find(".access_list");
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
                            dataType: "json",
                            url: "/ajax/user_list/",
                            success: function(users2) {
                                var autocompleteHandler = function(usersForHandler, query, callback) {
                                    return callback(userAutocompleteHandler(query, usersForHandler));
                                };
                                $("#id_adduser").typeahead({
                                    "source": autocompleteHandler.bind(this, users2),
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
                }); // end member_list_user_toggle

                // todo this is a duplicate function..
                $(".remove_group").unbind("click");
                $(".remove_group").click(function() {
                    var href = $(this).attr("href");
                    var removeGroup = $(this);

                    $.ajax({
                        global: false,
                        url: href,
                        success: function() {
                            removeGroup.fadeOut(300, function() {
                                removeGroup.parents(".access_list_group").remove();
                            });
                        },
                        error: function(jqXHR, textStatus, errorThrown) {
                            alert(jqXHR.responseText);
                        },
                        complete: function() {
                            groupMessagesDiv.hide().html("");
                        }
                    }); // end ajax
                    return false;
                }); // end remove group
            },
            error: function(jqXHR, textStatus, errorThrown) {
                if (jqXHR.status === 400) {
                    groupMessagesDiv.hide().html(jqXHR.responseText).fadeIn();
                    return;
                }
                groupMessagesDiv.hide().html("");
                alert("Error adding group!");
            }
        });
        return false;
    });

    $(".remove_group").unbind("click");
    $(".remove_group").click(function() {

        var href = $(this).attr("href");

        var removeGroup = $(this);

        $.ajax({
            global: false,
            url: href,
            success: function() {
                removeGroup.fadeOut(300, function() {
                    removeGroup.parents(".access_list_group").remove();
                });
            },
            error: function(jqXHR, textStatus, errorThrown) {
                alert(jqXHR.responseText);
            },
            complete: function() {
                $("#group-sharing-messages").hide().html("");
            }
        }); // end ajax

        return false;
    }); // end remove group

};

export function addGroupSharingEventHandlers() {
    $(".share_link_group").unbind("click");
    $(".share_link_group").bind("click", function(evt) {
        var modal = $("#modal-share-group");

        modal.find(".modal-body").html("");
        modal.find(".loading-placeholder").show();
        modal.modal("show");

        var groupSharingModalContentUrl = "/experiment/control_panel/" +
                                          $("#experiment-id").val() +
                                          "/access_list/group/";
        modal.find(".modal-body")
            .load(groupSharingModalContentUrl, groupSharingModalLoaded);
    });

    $("#modal-share-group").bind("hidden.bs.modal", function() {
        loadExpTabPane("sharing");
    });
}

export function expSharingAjaxReady() {

    // user access list
    var $targetUser = $("#experiment_user_list");
    $targetUser.html(loadingHTML + "</br>");
    var href = "/experiment/control_panel/" + $("#experiment-id").val() + "/access_list/user/readonly/";
    $targetUser.load(href);

    // group access list
    var $targetGroup = $("#experiment_group_list");
    $targetGroup.html(loadingHTML + "</br>");
    href = "/experiment/control_panel/" + $("#experiment-id").val() + "/access_list/group/readonly/";
    $targetGroup.load(href);

    // token access list
    var $targetToken = $("#experiment_token_list");
    $targetToken.html(loadingHTML + "</br>");
    href = "/experiment/control_panel/" + $("#experiment-id").val() + "/access_list/tokens/";
    $targetToken.load(href);

    $(document).on("click", ".token_delete", function(evt) {
        var delRow = $(this).parents("tr");
        evt.preventDefault();
        $.post(this.href, { csrfmiddlewaretoken: $("#csrf-token").val()}, function()
        {
            delRow.remove();
        });
    });

    $(".create_token_link").unbind("click");
    $(".create_token_link").bind("click", function(evt) {
        evt.preventDefault();
        var $targetToken = $("#experiment_token_list"); // eslint-disable-line no-shadow
        $targetToken.html(loadingHTML + "</br>");
        $.post(this.href, {csrfmiddlewaretoken: $("#csrf-token").val()}, function(data)
        {
            // eslint-disable-next-line no-shadow
            var href = "/experiment/control_panel/" + $("#experiment-id").val() + "/access_list/tokens/";
            $targetToken.load(href);
        }); // TODO error-handling
    });
    addUserSharingEventHandlers();
    addGroupSharingEventHandlers();
}
