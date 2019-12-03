/* Hide or show an experiment's full description */

$(document).ready(function() {
    // Abbreviate abstract
    var hideAbstract = false;
    var spanhtml = $("#abstractHolder").html();

    if(spanhtml.split("<br>").length > 1 || spanhtml.length > 100)
    {
        hideAbstract = true;
        $("#abstract-toggle").attr("style", "display: inline; color: black;");

        $("#abstractText").empty().html(spanhtml);
        $("#abstractText").parent().attr("style", "height: 60px;");
        $("#abstractText").parent().addClass("abstract-clickable");

        $(document).on("click", "#abstract-toggle", function(evt) {
            if(!hideAbstract)
            {
                $("#abstractText").parent().attr("style", "height: 60px;");
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
    else if (!spanhtml)
    {
        $("#abstractText").parent().attr("style", "height: 30px;");
        $("#abstract-toggle").attr("style", "display: none;");
    }
    else
    {
        $("#abstractText").html(spanhtml);
        $("#abstract-toggle").attr("style", "display: none;");
    }
});

