$(document).ready(function(){
    var users = (function () {
        var val = null;
        var authMethod = "localdb";
        var data = { authMethod: authMethod };
        $.ajax({
            // Ouch! This should be rewritten to handle async.
            'async': false,
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
                val = list;
            }
         });
        return val;
    })();


    $("#id_q").autocomplete(users, {
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


    var myClose = function(hash) {
            hash.w.fadeOut('2000',function(){ hash.o.remove()});
            window.location.hash = "";
        };

    $("#jqmAlertStatus").jqm({modal: false, overlay: 1,onHide:myClose});

    // Add status messages for create/save
    if (window.location.hash) {
        if(window.location.hash == '#created')
        {
            $('#jqmStatusMessage').html('Experiment Created');
        }
        else if(window.location.hash == '#saved')
        {
            $('#jqmStatusMessage').html('Experiment Saved');
        }
    }

    // Show status message if there's one to show
    if ($('#jqmStatusMessage').text() != '') {
        $('#jqmAlertStatus').jqmShow();
    }

    // Hover events
    $('.ui-state-default').live('mouseover mouseout', function(evt) {
        if (evt.type == 'mouseover') {
            $(this).addClass('ui-state-hover');
        } else {
            $(this).removeClass('ui-state-hover');
        }
    });

});



