import {
    handleExpAccordionLink
} from "../experiment-accordion";

$(document).ready(function() {
    $("#experiments .accordion-body").collapse({parent: "#experiments", toggle: true});
    $(".explink").on("click", handleExpAccordionLink);
    $(".dllink").on("click", function(e) {
        e.stopPropagation();
    });
});

