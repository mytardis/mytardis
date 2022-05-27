$(document).on("click", "a.push-to", function(e) {
    e.preventDefault();
    window.open(
        $(e.target).attr("href"),
        "push-to",
        "width=800, height=600"
    );
});
