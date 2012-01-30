jasmine.getFixtures().fixturesPath = "/jasmine/fixtures/";

describe("Main", function() {

	describe("search box autocompletion", function() {
	    it("should activate autocompletion for #id_q", function() {
	        loadFixtures("search_autocomplete.html");
	        expect($('#id_q')).toExist();
	        activateSearchAutocomplete();
	        waitsFor(function() {
	        	return $('#id_q[autocomplete]').size() > 0;
	        }, "Should be activated by now.", 500);
	        runs(function() {
		        expect($('#id_q')).toHaveAttr('autocomplete');
		        expect($('#id_q')).toHaveClass('ac_input');
	        });
	    });
	});


	describe("alert status", function() {
	    it("should show an alert box when status is set", function() {
	        loadFixtures("status_message_populated.html");
	        expect($('#jqmStatusMessage')).toHaveText('Test message');
	        expect($('#jqmAlertStatus')).toBeVisible();
	        activateAlertStatus();
	        expect($('#jqmStatusMessage')).toHaveText('Test message');
	        expect($("#jqmAlertStatus")).toBeVisible();
	        $(".jqmClose").click();
	        waitsFor(function() {
	        	return $('#jqmAlertStatus').is(':hidden');
	        }, "Alert should be hidden by now.", 3000);
	    });

	    it("should show an alert box when hash is #created", function() {
	        loadFixtures("status_message_unpopulated.html");
	        expect($('#jqmStatusMessage')).toHaveText('');
	        expect($('#jqmAlertStatus')).toBeVisible();
	        window.location.hash = '#created';
	        activateAlertStatus();
	        expect($('#jqmStatusMessage')).toHaveText('Experiment Created');
	        expect($("#jqmAlertStatus")).toBeVisible();
	        expect(window.location.hash).toEqual('#created');
	        $(".jqmClose").click();
	        waitsFor(function() {
	        	return $('#jqmAlertStatus').is(':hidden');
	        }, "Alert should be hidden by now.", 3000);
	        expect(window.location.hash).toEqual('');
	    });

	    it("should show an alert box when hash is #saved", function() {
	        loadFixtures("status_message_unpopulated.html");
	        expect($('#jqmStatusMessage')).toHaveText('');
	        expect($('#jqmAlertStatus')).toBeVisible();
	        window.location.hash = '#saved';
	        activateAlertStatus();
	        expect($('#jqmStatusMessage')).toHaveText('Experiment Saved');
	        expect($("#jqmAlertStatus")).toBeVisible();
	        expect(window.location.hash).toEqual('#saved');
	        $(".jqmClose").click();
	        waitsFor(function() {
	        	return $('#jqmAlertStatus').is(':hidden');
	        }, "Alert should be hidden by now.", 3000);
	        expect(window.location.hash).toEqual('');
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

});