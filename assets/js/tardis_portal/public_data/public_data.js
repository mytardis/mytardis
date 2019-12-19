$(document).ready(function() {
    $("#experiments .accordion-body").collapse({parent: "#experiments", toggle: true});
    $(".explink").on("click", function(e) {
        e.stopPropagation();
    });
    $(".dllink").on("click", function(e) {
        e.stopPropagation();
    });
});

