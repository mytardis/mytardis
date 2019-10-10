/* eslint no-underscore-dangle: 0 */
/* global _, Backbone, Mustache */

// Remove buttons from templates
_.each(["publication", "website"], function(v) {
    var tmpl = $("<div/>").html(Mustache.TEMPLATES["related_info/" + v]);
    tmpl.find("button").remove();
    Mustache.TEMPLATES["related_info/" + v] = tmpl.html();
});

var RelatedInfoModel = Backbone.Model.extend({});

var RelatedInfo = Backbone.Collection.extend({
    model: RelatedInfoModel,
    url: "/apps/related-info/experiment/" + $("#experiment-id").val() + "/related-info/"
});
var relatedInfo = new RelatedInfo();

var refreshItemDisplay = function(msg) {
    $("#related-info-items").empty();
    relatedInfo.each(function(v, k) {
        var template = "related_info/" + v.get("type");
        var item = $("<div/>")
            .addClass("related-info-item")
            .prop("model", v)
            .html(Mustache.to_html(
                Mustache.TEMPLATES[template],
                v.attributes, Mustache.TEMPLATES));
        $("#related-info-items").append(item);
    });
};

relatedInfo.on("add", refreshItemDisplay);
relatedInfo.on("change", refreshItemDisplay);
relatedInfo.on("destroy", refreshItemDisplay);

relatedInfo.fetch({ success: refreshItemDisplay });
