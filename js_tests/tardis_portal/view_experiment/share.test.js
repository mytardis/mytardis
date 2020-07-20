/* global QUnit, _ */

import {
    addUserSharingEventHandlers,
    addGroupSharingEventHandlers
} from "../../../assets/js/tardis_portal/view_experiment/share/share.js";

// Tests for assets/js/tardis_portal/view_experiment/share/share.js
// which used to be embedded within
// tardis/tardis_portal/templates/tardis_portal/ajax/share.html

require("jquery-mockjax/dist/jquery.mockjax")(jQuery, window);

QUnit.module("tardis_portal.ajax.share", {
    beforeEach: function(assert) {
        $.ajaxSetup({ async: false });
    },
    afterEach: function(assert) {
        $.ajaxSetup({ async: true });
    }
});



QUnit.test("Test clicking on Change User Sharing button", function(assert) {

    $("#qunit-fixture").append(`
        <input type="hidden" id="experiment-id" value="1">

        <a class="share_link btn btn-mini"
           title="Change">
          <i class="fa fa-share"></i>
          Change User Sharing
        </a>

        <!-- sharing user modal !-->
        <div class="modal hide fade" id="modal-share">
          <!-- ... -->
          <div class="modal-body"></div>
        </div>`);

    var userAccessPanelHtml = `
        <div class="access_list1">
          <div class="users">
            <h3>Current User Permissions</h3>
            <!-- ... -->
          </div> <!-- users -->
          <h3>Add new user</h3>
          <!-- ... -->
          Username:
          <!-- ... -->
          Permissions:
          <!-- ... -->
        </div>`;

    $.mockjax({
        url: "/experiment/control_panel/1/access_list/user/",
        contentType: "text/html",
        responseText: userAccessPanelHtml
    });

    $.mockjax({
        url: "/ajax/user_list/",
        contentType: "test/json",
        responseText: `[{
            "username": "testuser1",
            "first_name": "Test",
            "last_name": "User1",
            "email": "testuser1@example.com",
            "auth_methods": ["testuser1:localdb:Local DB"]
        }]`
    });

    // addUserSharingEventHandlers needs to be run after the QUnit fixtures
    // have been created so that jQuery can find the elements to bind events to:
    addUserSharingEventHandlers();

    var modalShareBody = $("#qunit-fixture").find("#modal-share").find(".modal-body");
    assert.equal(modalShareBody.html(), "");
    var shareLink = $("#qunit-fixture").find(".share_link");
    shareLink.click();

    // Below, we check if the panel's heading can be found within the
    // modal-body div's HTML, i.e. ensuring that indexOf doesn't return -1:
    assert.notEqual(modalShareBody.html().indexOf("<h3>Current User Permissions</h3>"), -1);
});

QUnit.test("Test clicking on Change Group Sharing button", function(assert) {

    $("#qunit-fixture").append(`
        <input type="hidden" id="experiment-id" value="1">`);

    $("#qunit-fixture").append(`
        <a class="share_link_group btn btn-mini" title="Change">
          <i class="fa fa-share"></i>
          Change Group Sharing
        </a>`);

    $("#qunit-fixture").append(`
        <!-- sharing group modal !-->
        <div class="modal hide fade" id="modal-share-group">
          <!-- ... -->
          <div class="modal-body"></div>
        </div>`);

    var groupAccessPanelHtml = `
        <div class="access_list2">
          <div class="groups">
            <!-- ... -->
          </div> <!-- groups -->
          <strong><label>Add group to experiment: </label></strong>
          <!-- ... -->
        </div>`;

    $.mockjax({
        url: "/experiment/control_panel/1/access_list/group/",
        contentType: "text/html",
        responseText: groupAccessPanelHtml
    });

    // Real response would come from
    // tardis.tardis_portal.views.authorisation.retrieve_group_list
    $.mockjax({
        url: "/ajax/group_list/",
        contentType: "test/plain",
        responseText: "testgroup1 ~ testgroup2"
    });

    // addGroupSharingEventHandlers needs to be run after the QUnit fixtures
    // have been created so that jQuery can find the elements to bind events to:
    addGroupSharingEventHandlers();

    var modalShareGroupBody = $("#qunit-fixture").find("#modal-share-group").find(".modal-body");
    assert.equal(modalShareGroupBody.html(), "");
    var shareLinkGroup = $("#qunit-fixture").find(".share_link_group");
    shareLinkGroup.click();

    // Below, we check if the panel's heading can be found within the
    // modal-body div's HTML, i.e. ensuring that indexOf doesn't return -1:
    assert.notEqual(modalShareGroupBody.html().indexOf("Add group to experiment:"), -1);
});
