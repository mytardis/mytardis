jasmine.getFixtures().fixturesPath = "/jasmine/fixtures/";

describe("Main", function() {

  describe("login detection", function() {
      it("should use user menu to determine state", function() {
          // Check we get false if the user menu is absent
          expect($('#user-menu')).not.toExist();
          expect(isLoggedIn()).toBe(false);
          // Check we get true if the user menu is present
          $('body').append($('<div id="user-menu"></div>'));
          expect($('#user-menu')).toExist();
          expect(isLoggedIn()).toBe(true);
          // Check that removing the user menu changes response
          $('#user-menu').remove();
          expect(isLoggedIn()).toBe(false);
      });
  });

  describe("search box typeahead", function() {
      it("should activate typeahead for #id_q", function() {
          loadFixtures("search_autocomplete.html");
          expect($('#id_q')).toExist();
          expect($('#id_q').data('typeahead')).toBeUndefined();
          activateSearchAutocomplete();
          waitsFor(function() {
            return typeof($('#id_q').data('typeahead')) != 'undefined' ;
          }, "Should be activated by now.", 500);
          runs(function() {
            expect($('#id_q').data('typeahead').options.items).toBe(10);
          });
      });
  });

  describe("hover detection", function() {
      it("should add/remove class on mouseover/mouseout", function() {
          setFixtures('<div id="hover_detect" class="ui-state-default"></div>');
          expect($('#hover_detect')).toExist();
          activateHoverDetection();
          expect($('#hover_detect')).not.toHaveClass('ui-state-hover');
          $('#hover_detect').trigger('mouseover');
          expect($('#hover_detect')).toHaveClass('ui-state-hover');
          $('#hover_detect').trigger('mouseout');
          expect($('#hover_detect')).not.toHaveClass('ui-state-hover');
      });

  });

  describe("user autocompletion handler", function() {
    it("should search a list of users", function() {
      var testData = [
        {
          "username": "testuser1",
          "first_name": "Test",
          "last_name": "User",
          "email": "testuser1@example.test",
          "auth_methods": ["testuser:localdb:Local DB"]
        },
        {
          "username": "testuser2",
          "first_name": "Test",
          "last_name": "User",
          "email": "",
          "auth_methods": ["testuser2:localdb:Local DB"]
        },
        {
          "username": "testuser3",
          "first_name": "",
          "last_name": "",
          "email": "testuser3@example.test",
          "auth_methods": ["testuser3:localdb:Local DB"]
        },
        {
          "username": "testuser4",
          "first_name": "",
          "last_name": "",
          "email": "",
          "auth_methods": ["testuser4:localdb:Local DB"]
        },
        {
          "username": "testuser5",
          "first_name": "Test",
          "last_name": "User",
          "email": "testuser5@example.test",
          "auth_methods": ["testuser5:otherdb:Other DB"]
        }
      ];
      // Basic query checks
      expect(userAutocompleteHandler("test", testData, 'localdb')).toEqual([
        {
          'label': 'Test User [testuser1] <testuser1@example.test>',
          'value': 'testuser1'
        },
        {
          'label': 'Test User [testuser2]',
          'value': 'testuser2'
        },
        {
          'label': '[testuser3] <testuser3@example.test>',
          'value': 'testuser3'
        },
        {
          'label': '[testuser4]',
          'value': 'testuser4'
        }
      ]);
      expect(userAutocompleteHandler("testuser1", testData, 'localdb')).toEqual([
        {
          'label': 'Test User [testuser1] <testuser1@example.test>',
          'value': 'testuser1'
        }
      ]);
    });
  });

});