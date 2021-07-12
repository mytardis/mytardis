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

QUnit.skip("Test clicking on Public Access button", function(assert) {

    $("#qunit-fixture").append(`
        <input type="hidden" id="experiment-id" value="1">
        
        <button class="public_access_button btn btn-outline-secondary btn-sm" 
                data-bs-toggle="modal"
                data-bs-target="#modal-public-access"
                title="Change" 
                type="submit">
              <i class="fa fa-cog me-1"></i>
              Change Public Access
        </button>

        <!-- public access modal !-->
        <div class="modal hide fade" id="modal-public-access">
          <!-- ... -->
          <div class="modal-body"></div>
        </div>
   
        <div class="modal hide fade" id="modal-metadata">
          <div class="modal-header">
            <a class="close" data-dismiss="modal">&times;</a>
            <h1 class="title">Add Parameters</h1>
          </div>

          <div class="loading-placeholder" style="display: none">
            <p>Please wait... <img src="/static/images/ajax-loader.gif" alt="loading" /></p>
          </div>

          <div class="modal-body"></div>

          <div class="modal-footer">
            <button class="submit-button btn btn-success">
              <i class="fa fa-ok"></i>
              Save
            </button>
          </div>
        </div>`);

    $.mockjax({
        url: "/ajax/experiment/1/rights",
        contentType: "text/json",
        responseText:
        `{
            "public_access": 100,
            "license": 1,
            "legal_text": "No Legal Agreement Specified"
        }`,
    });

    $.mockjax({
        url: "/static/publishing_legal.txt",
        contentType: "text/plain",
        responseText:
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
    });

    $.mockjax({
        url: "/ajax/license/list?public_access=1",
        contentType: "text/json",
        responseText: `[{
            "name": "Unspecified License",
            "url": "http://en.wikipedia.org/wiki/Copyright#Exclusive_rights",
            "is_active": true,
            "allows_distribution": false,
            "internal_description": "\n No license is explicitly specified. You implicitly retain all rights\n under copyright.\n ",
            "image_url": "", 
            "id": ""
        }]`
    });

    $.mockjax({
        url: "/search/parameter_field_list/?authMethod=localdb",
        contentType: "text/plain",
        responseText:
            "Test User1:username+Test User2:username+" +
            "dataset_id_stored:search_field+" +
            "experiment_id_stored:search_field+" +
            "datafile_filename:search_field"
    });

    // Check that underscore library is loaded
    // as it is required to load view_experiment/experiment-tabs.js:
    assert.ok(_.isEmpty({}));

    var modalPublicAccessBody = $("#qunit-fixture").find("#modal-public-access").find(".modal-body");
    assert.equal(modalPublicAccessBody.html(), "");
    var publicAccessLink = $("#qunit-fixture").find(".public_access_button");
    publicAccessLink.click();

    // Below, we check if the panel's heading can be found within the
    // modal-body div's HTML, i.e. ensuring that indexOf doesn't return -1:
    assert.notEqual(modalPublicAccessBody.html().indexOf("<h3>Step 1: Change Public Access:</h3>"), -1);
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
