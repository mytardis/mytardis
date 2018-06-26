/* tardis/tardis_portal/static/js/jquery/tardis_portal/ajax/share.js */

/* eslint global-strict: 0, strict: 0 */
/* global userAutocompleteHandler, _ */

var loadingHTML = "<img src=\"/static/images/ajax-loader.gif\"/><br />";


$(".public_access_link").unbind("click");
$(".public_access_link").bind("click", function(evt) {
    var modal = $("#modal-public-access");

    modal.find(".modal-body").html("");
    modal.find(".loading-placeholder").show();
    modal.modal("show");

    modal.find(".modal-body")
        .load("/ajax/experiment/" + $("#experiment-id").val() + "/rights", function(response, status, xhr) {
            modal.find(".loading-placeholder").hide();

            if (status == "error") {
                $(this).html(response);
            }

            $("#legal-section").hide();
        });

});


$("#modal-public-access").bind("hidden", function() {
    $(".tab-pane").trigger("experiment-change");
});


// beginswith, endswith
String.prototype.beginsWith = function(t, i) {
    if (i == false) {
        return (t == this.substring(0, t.length));
    } else {
        return (t.toLowerCase() == this.substring(0, t.length).toLowerCase());
    }
};

String.prototype.endsWith = function(t, i) {
    if (i == false) {
        return (t == this.substring(this.length - t.length));
    } else {
        return (t.toLowerCase() == this.substring(this.length - t.length).toLowerCase());
    }
};

// user sharing modal

$(".share_link").unbind("click");
$(".share_link").bind("click", function(evt) {
    var modal = $("#modal-share");

    modal.find(".modal-body").html("");
    modal.find(".loading-placeholder").show();
    modal.modal("show");

    modal.find(".modal-body")
        .load("/experiment/control_panel/" + $("#experiment-id").val() + "/access_list/user/", function() {
            modal.find(".loading-placeholder").hide();

            $("#id_entered_user").keypress(function(e) {
                // Reset autocomplete user when typing in the user edit field.
                $(this).siblings("#id_autocomp_user").val("");
                $(this).siblings("#id_authMethod").attr("disabled", "");

                if (e.keyCode == 13)
                {
                    $("#user.form_submit").click();
                }
            });
            // Load user list and activate field autocompletion
            $.ajax({
                "dataType": "json",
                "url": "/ajax/user_list/",
                "success": function(users) {
                    if($("select#id_authMethod option").length == 1) {
                        $("#id_authMethod_label").hide();
                        $("#id_authMethod").hide();
                    }
                    $("#id_entered_user").autocomplete({
                        "source": _.bind( function(query, callback) {
                            var authMethod = $("#id_authMethod").val();
                            callback(
                                userAutocompleteHandler(
                                    query.term, this.users, authMethod));
                        }, { "users": users })
                    });
                }
            });


            $("#user.form_submit").unbind("click");
            $("#user.form_submit").click(function(event) {
                event.preventDefault();
                var entered_user = $(this).siblings("#id_entered_user").val();
                var autocomp_user = $(this).siblings("#id_autocomp_user").val();
                var username = null;
                var authMethod = null;
                if (autocomp_user != "") {
                    // Use the details from the autocomplete.
                    autocomp_user = autocomp_user.split(":");
                    username = autocomp_user[0];
                    authMethod = autocomp_user[1];
                } else {
                    // Autocomplete failed. Use the entered username as-is.
                    username = entered_user;
                    authMethod = $(this).siblings("#id_authMethod").val();
                }
                var users_div = $(this).parents(".access_list1").children(".users");

                var permissions = $(this).siblings("#id_permission").val();

                var canRead = false;
                var canWrite = false;
                var isOwner = false;
                var canDelete = false;
                if (permissions == "read")
                {
                    canRead = true;
                }
                else if (permissions == "edit")
                {
                    canRead = true;
                    canWrite = true;
                }
                else if (permissions == "owner")
                {
                    canRead = true;
                    canWrite = true;
                    isOwner = true;
                    canDelete = true;
                }

                permissions = "/?authMethod=" + authMethod + "&canRead=" + canRead + "&canWrite=" + canWrite + "&canDelete=" + canDelete + "&isOwner=" + isOwner;
                var action = "/experiment/control_panel/" + $("#experiment-id").val() +
                    "/access_list/add/user/" + username + permissions;

                $.ajax({
                    "async": false,
                    "global": true,
                    type: "GET",
                    url: action,
                    success: function(data) {
                        users_div.hide().append(data).fadeIn();
                        // todo this is a duplicate function..
                        $(".remove_user").unbind("click");
                        $(".remove_user").click(function() {
                            var href = $(this).attr("href");
                            var remove_user = $(this);
                            $.ajax({
                                "async": false,
                                "global": false,
                                "url": href,
                                "success": function(data2) {
                                    var val = data2;
                                    if(val == "OK") {
                                        remove_user.fadeOut(300, function() { remove_user.parents(".access_list_user").remove(); });
                                    }
                                    else { alert(val); }
                                }
                            }); // end ajax
                            return false;
                        }); // end remove user
                    },
                    error: function(data) { alert("Error adding user"); }
                });
                return false;
            });

            $(".remove_user").unbind("click");
            $(".remove_user").click(function() {
                var href = $(this).attr("href");
                var remove_user = $(this);
                $.ajax({
                    "async": false,
                    "global": false,
                    "url": href,
                    "success": function(data) {
                        var val = data;
                        if(val == "OK") {
                            remove_user.fadeOut(300, function() { remove_user.parents(".access_list_user").remove(); });
                        }
                        else { alert(val); }
                    }
                }); // end ajax
                return false;
            }); // end remove user
        });

});

$("#modal-share").bind("hidden", function() {
    $(".tab-pane").trigger("experiment-change");
});

$("#modal-share-group").bind("hidden", function() {
    $(".tab-pane").trigger("experiment-change");
});


// group sharing modal

$(".share_link_group").unbind("click");
$(".share_link_group").bind("click", function(evt) {
    var modal = $("#modal-share-group");


    modal.find(".modal-body").html("");
    modal.find(".loading-placeholder").show();
    modal.modal("show");

    modal.find(".modal-body")
        .load("/experiment/control_panel/" + $("#experiment-id").val() + "/access_list/group/", function() {
            modal.find(".loading-placeholder").hide();

            var users = null; // eslint-disable-line no-unused-vars

            var groups = (function() {
                var val = null;
                $.ajax({
                    "async": false,
                    "global": false,
                    "url": "/ajax/group_list/",
                    "success": function(data) { val = data; }
                });
                return val;
            })();

            $("#id_addgroup").keypress(function(e) {
                if (e.keyCode == 13)
                {
                    $("#group.form_submit").click();
                }
            });

            // TODO: Replace with Bootstrap typeahead
            $(".groupsuggest").typeahead({
                "source": groups.split(" ~ ")
            });


            // view group members
            $(".member_list_user_toggle").unbind("click");
            $(".member_list_user_toggle").bind("click", function(evt2) {
                evt2.preventDefault();

                var icon = $(this).find("i");
                icon.toggleClass("fa fa-folder-open icon-folder-close");
                $(this).toggleClass("members-shown members-hidden");

                var user_list = $(this).parents(".group").find(".access_list");
                // If not showing members, just hide user list
                if (!$(this).hasClass("members-shown")) {
                    user_list.hide();
                    return;
                }

                user_list.html(loadingHTML);
                // Load (jQuery AJAX "load()") and show access list
                user_list.load(this.href, function() {
                    // Load user list and activate field autocompletion
                    $.ajax({
                        "dataType": "json",
                        "url": "/ajax/user_list/",
                        "success": function(users2) {
                            $("#id_adduser").autocomplete({
                                "source": _.bind( function(query, callback) {
                                    var authMethod = $("#id_authMethod").val();
                                    callback(
                                        userAutocompleteHandler(
                                            query.term, this.users, authMethod));
                                }, { "users": users2 })
                            });
                        }
                    });
                }).show();
            });

            $("#group.form_submit").unbind("click");
            $("#group.form_submit").click(function(event) {
                event.preventDefault();

                // TODO: shift group creation to group management page
                // var usersuggest = $(this).parents('.access_list2').find(".usersuggest").val();
                var groupsuggest = $(this).parents(".access_list2").find(".groupsuggest").val();
                // var authMethod = $(this).parents('.access_list2').find("#id_authMethod").val();
                var groups_div = $(this).parents(".access_list2").children(".groups");
                // var create = $(this).parents('.access_list2').find(".creategroup").is(':checked');
                // var canRead = $(this).parents('.access_list2').find(".canRead").is(':checked');
                // var canWrite = $(this).parents('.access_list2').find(".canWrite").is(':checked');
                // var canDelete = $(this).parents('.access_list2').find(".canDelete").is(':checked');
                // var permissions = '/?authMethod=' + authMethod + '&create=' + create + '&canRead=' + canRead + '&canWrite=' + canWrite + '&canDelete=' + canDelete + '&admin=' + usersuggest;

                var action = "/experiment/control_panel/" + $("#experiment-id").val() + "/access_list/add/group/" + groupsuggest;

                var permissions = $(this).siblings("#id_permission_group").val();

                var canRead = false;
                var canWrite = false;
                var isOwner = false;
                var canDelete = false;
                if(permissions == "read")
                {
                    canRead = true;
                }
                else if(permissions == "edit")
                {
                    canRead = true;
                    canWrite = true;
                }
                else if(permissions == "owner")
                {
                    canRead = true;
                    canWrite = true;
                    isOwner = true;
                    canDelete = true;
                }

                permissions = "/?canRead=" + canRead + "&canWrite=" + canWrite + "&canDelete=" + canDelete + "&isOwner=" + isOwner;
                action = action + permissions;

                $.ajax({
                    "async": false,
                    "global": true,
                    type: "GET",
                    url: action,
                    success: function(data) {
                        groups_div.hide().append(data).fadeIn();

                        // view group members
                        $(".member_list_user_toggle").unbind("click");
                        $(".member_list_user_toggle").bind("click", function(evt2) {
                            evt2.preventDefault();

                            var icon = $(this).find("i");
                            icon.toggleClass("fa fa-folder-open icon-folder-close");
                            $(this).toggleClass("members-shown members-hidden");

                            var user_list = $(this).parents(".access_list_group").find(".access_list");
                            // If not showing members, just hide user list
                            if (!$(this).hasClass("members-shown")) {
                                user_list.hide();
                                return;
                            }

                            user_list.html(loadingHTML);
                            // Load (jQuery AJAX "load()") and show access list
                            user_list.load(this.href, function() {
                                // Load user list and activate field autocompletion
                                $.ajax({
                                    "dataType": "json",
                                    "url": "/ajax/user_list/",
                                    "success": function(users2) {
                                        $("#id_adduser").autocomplete({
                                            "source": _.bind( function(query, callback) {
                                                var authMethod = $("#id_authMethod").val();
                                                callback(
                                                    userAutocompleteHandler(
                                                        query.term, this.users, authMethod));
                                            }, { "users": users2 })
                                        });
                                    }
                                });
                            }).show();
                        }); // end member_list_user_toggle

                        // todo this is a duplicate function..
                        $(".remove_group").unbind("click");
                        $(".remove_group").click(function() {
                            var href = $(this).attr("href");
                            var remove_group = $(this);
   
                            $.ajax({
                                "async": false,
                                "global": false,
                                "url": href,
                                "success": function(data2) {
                                    var val = data2;
                                    if(val == "OK") {
                                        remove_group.fadeOut(300, function() {
                                            remove_group.parents(".access_list_group").remove();
                                        });
                                    }
                                    else { alert(val); }
                                }
                            }); // end ajax
                            return false;
                        }); // end remove group
                    },
                    error: function(data) { alert("Error adding group!"); }
                });
                return false;
            });

            $(".remove_group").unbind("click");
            $(".remove_group").click(function() {

                var href = $(this).attr("href");

                var remove_group = $(this);

                $.ajax({
                    "async": false,
                    "global": false,
                    "url": href,
                    "success": function(data) {
                        var val = data;
                        if(val == "OK") {
                            remove_group.fadeOut(300, function() {
                                remove_group.parents(".access_list_group").remove();
                            });
                        }
                        else { alert("val"); }
                    }
                }); // end ajax

                return false;
            }); // end remove group

        });
});

$(document).ready(function() {

    // user access list
    var $target_user = $("#experiment_user_list");
    $target_user.html(loadingHTML + "</br>");
    var href = "/experiment/control_panel/" + $("#experiment-id").val() + "/access_list/user/readonly/";
    $target_user.load(href);

    // group access list
    var $target_group = $("#experiment_group_list");
    $target_group.html(loadingHTML + "</br>");
    href = "/experiment/control_panel/" + $("#experiment-id").val() + "/access_list/group/readonly/";
    $target_group.load(href);

    // token access list
    var $target_token = $("#experiment_token_list");
    $target_token.html(loadingHTML + "</br>");
    href = "/experiment/control_panel/" + $("#experiment-id").val() + "/access_list/tokens/";
    $target_token.load(href);


    $(".token_delete").live("click", function(evt) {
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
        var $target_token = $("#experiment_token_list"); // eslint-disable-line no-shadow
        $target_token.html(loadingHTML + "</br>");
        $.post(this.href, {csrfmiddlewaretoken: $("#csrf-token").val()}, function(data)
        {
            // eslint-disable-next-line no-shadow
            var href = "/experiment/control_panel/" + $("#experiment-id").val() + "/access_list/tokens/";
            $target_token.load(href);
        }); // TODO error-handling
    });
});
