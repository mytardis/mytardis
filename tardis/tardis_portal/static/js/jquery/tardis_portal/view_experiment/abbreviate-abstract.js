/* tardis/tardis_portal/static/js/jquery/tardis_portal/view_experiment/abbreviate_abstract.js */
  
/* eslint global-strict: 0, strict: 0, no-unused-vars: [2, {"vars": "local", "args": "none"}] */


$(document).ready(function() {
    // Abbreviate abstract
    var hideAbstract = false;
    var spanhtml = $("#abstractHolder").html();

    if(spanhtml.length > 100)
    {
        hideAbstract = true;
        $("#abstract-toggle").attr("style", "display: inline;");

        $("#abstractText").empty().html(spanhtml);
        $("#abstractText").parent().attr("style", "height: 33px;");
        $("#abstractText").parent().addClass("abstract-clickable");

        $(document).on("click", "#abstract-toggle", function(evt) {
            if(!hideAbstract)
            {
                $("#abstractText").parent().attr("style", "height: 33px;");
                hideAbstract = true;
                $("#abstract-toggle").text("Show Description");
            }
            else
            {
                $("#abstractText").parent().attr("style", "padding-top:20px;");
                hideAbstract = false;
                $("#abstract-toggle").text("Hide Description");
            }
        });
    }
    else
    {
        $("#abstractText").html(spanhtml);
    }
});

