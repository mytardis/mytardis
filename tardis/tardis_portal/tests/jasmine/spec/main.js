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