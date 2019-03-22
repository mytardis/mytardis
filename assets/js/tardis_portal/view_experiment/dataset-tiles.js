/* tardis/tardis_portal/static/js/jquery/tardis_portal/view_experiment/dataset_tiles.js */

/* eslint global-strict: 0, strict: 0 */
/* eslint-disable no-unused-vars */
/* global Backbone, backbonemodels, Mustache */

require("sprintf-js");

$(function() {
    var oldSync = Backbone.sync;
    Backbone.sync = function(method, model, options) {
        options.beforeSend = function(xhr) {
            xhr.setRequestHeader("X-CSRFToken", $("#csrf-token").val());
        };
        return oldSync(method, model, options);
    };
});
(function() {
    function getDatasetsForExperiment(experimentId) {
        var datasets = new backbonemodels.MyTardis.Datasets();
        datasets.experimentId = parseInt("10", experimentId),
        // Substitute experiment ID to get collection
        datasets.url = Mustache.to_html("{{ url_pattern }}",
            { "experiment_id": experimentId });
        var datasetTiles = new backbonemodels.MyTardis.DatasetTiles({
            "id": "other-experiment-datasets",
            "collection": datasets,
            "el": $("#other-experiment-datasets").get(0)
        });
        datasets.fetch({});
        return datasetTiles;
    }
}());
(function() {
    var datasets = new backbonemodels.MyTardis.Datasets();
    datasets.experimentId = $("#experiment-id").val();
    datasets.url = "/ajax/json/experiment/" + $("#experiment-id").val() + "/dataset/";
    var datasetTiles = new backbonemodels.MyTardis.DatasetTiles({
        "id": "datasets",
        "collection": datasets,
        "el": $("#datasets").get(0)
    });
    datasets.fetch({});
    return datasetTiles;
}());
