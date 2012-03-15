var activateSearchAutocomplete = function() {
    var authMethod = "localdb";
    var data = { authMethod: authMethod };
    $.ajax({
        'global': false,
        'data': data,
        'url': '/ajax/parameter_field_list/',
        'success': function (data) {
            data = data.split("+");
            var list = new Array();
            $.each(data, function(i,l) {
                var name = l.split(":")[0];
                var type = l.split(":")[1];
                list[i] = [name, type];
            });
            $("#id_q").autocomplete(list, {
                matchContains: true,
                multiple: true,
                multipleSeparator: " ",
                selectFirst: false,
                autoFill: false,
                max: 10,
                minChars: 1,
                scroll: false,
                formatResult: function(item, position, length) {
                    if (item[1] == 'search_field')
                    {
                        return item[0] + ":";
                    }
                    else
                    {
                        return item[0];
                    }
                }
            });
        }
     });
};

var activateHoverDetection = function() {
	// Hover events
    $('.ui-state-default').live('mouseover mouseout', function(evt) {
        if (evt.type == 'mouseover') {
            $(this).addClass('ui-state-hover');
        } else {
            $(this).removeClass('ui-state-hover');
        }
    });
};

$(document).ready(function(){
	if ($('#id_q').length > 0) {
		activateSearchAutocomplete();
	}
	activateHoverDetection();
});
