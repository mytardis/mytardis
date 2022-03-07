/* assets/js/tardis_portal/view_dataset/keywords.js */

export function configureKeywordsSelect() {
    $(".keywords").select2({
        tags: true,
        tokenSeparators: [",", ";"],
        selectOnClose: true,
        placeholder: "Add keyword(s). Press enter after each.",
    }).on("select2:open", function(evt) {
        $(".select2-container--open .select2-dropdown--below").css("display", "none");
    });

    // If the "Edit Dataset" button is missing or hidden,
    // make the keywords read-only:
    if ($(`a[title="Edit Dataset"]`).css("display") !== "inline-block") {
        $(".keywords").select2({ disabled: "readonly" });
    }

    // Feel free to use your own styling here:
    $(".select2-selection").css({
        "border-width": "0px",
        "border-color": "gray",
        "background-color": "#fff",
        "line-height": "1.7",
        "letter-spacing": "0.5px"
    });
}

export function updateKeywords() {
    var tags = $(".keywords").select2("val");
    $.ajax({
        type: "PATCH",
        url: "/api/v1/dataset/" + $("#dataset-id").val() + "/",
        headers: {"X-CSRFToken": $("#csrf-token").val()},
        contentType: "application/json; charset=utf-8",
        data: JSON.stringify({tags: tags}),
        error: function(jqXHR, textStatus, errorThrown) {
            alert("Failed to update keywords");
        }
    });
}
