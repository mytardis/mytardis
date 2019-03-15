/* global QUnit, main, JSON */
"use strict";

// Tests for assets/js/tardis_portal/main.js

QUnit.module("tardis_portal.main", {
    beforeEach: function(assert) {
        $.ajaxSetup({ async: false });
    },
    afterEach: function(assert) {
        $.ajaxSetup({ async: true });
    }
});

QUnit.test("Test loading main.js", function(assert) {

    $.getScript("../assets/js/tardis_portal/main.js", function(data, textStatus, jqxhr) {
        assert.equal(jqxhr.status, 200);

    });
});

QUnit.test("Test userAutocompleteHandler", function(assert) {

    $.getScript("../assets/js/tardis_portal/main.js", function(data, textStatus, jqxhr) {
        assert.equal(jqxhr.status, 200);
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
        var actual = main.userAutocompleteHandler("Test", mockUsersList, "localdb");
        assert.equal(JSON.stringify(actual), JSON.stringify(expected));
    });
});
