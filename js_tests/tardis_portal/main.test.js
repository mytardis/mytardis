/* global QUnit, $ */

// Tests for assets/js/tardis_portal/main.js

import {userAutocompleteHandler} from "../../assets/js/tardis_portal/main";

QUnit.module("tardis_portal.main", {
    beforeEach: function(assert) {
        $.ajaxSetup({async: false});
    },
    afterEach: function(assert) {
        $.ajaxSetup({async: true});
    }
});

QUnit.test("Test userAutocompleteHandler", function(assert) {

    var mockUsersList = [
        {
            "username": "testuser1",
            "first_name": "Test",
            "last_name": "User1",
            "email": "testuser1@example.com",
            "auth_methods": ["testuser1:localdb:Local DB"]
        },
        {
            "username": "testuser2",
            "first_name": "Test",
            "last_name": "User2",
            "email": "testuser2@example.com",
            "auth_methods": ["testuser2:localdb:Local DB"]
        },
        {
            "username": "anotheruser",
            "first_name": "Another",
            "last_name": "User",
            "email": "anotheruser@example.com",
            "auth_methods": ["anotheruser:localdb:Local DB"]
        }
    ];
    var expected = [
        {
            "label": "Test User1 [testuser1] <testuser1@example.com>",
            "value": "testuser1"
        },
        {
            "label": "Test User2 [testuser2] <testuser2@example.com>",
            "value": "testuser2"
        }
    ];
    var actual = userAutocompleteHandler("Test", mockUsersList);
    assert.equal(JSON.stringify(actual), JSON.stringify(expected));
});
