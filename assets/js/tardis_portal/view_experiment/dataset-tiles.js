/* global Backbone, Mustache */

import "sprintf-js";
import {MyTardis} from "../backbone-models";

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

    var datasets = new MyTardis.Datasets();

    datasets.experimentId = $("#experiment-id").val();
    datasets.url = "/ajax/json/experiment/" + $("#experiment-id").val() + "/dataset/";

    var datasetTiles = new MyTardis.DatasetTiles({
        "id": "datasets",
        "collection": datasets,
        "el": $("#datasets").get(0)
    });

    datasets.fetch({});

    return datasetTiles;
}());

(function() {

    // eslint-disable-next-line no-unused-vars
    function getDatasetsForExperiment(experimentId) {
        var datasets = new MyTardis.Datasets();
        datasets.experimentId = parseInt("10", experimentId),
        // Substitute experiment ID to get collection
        datasets.url = Mustache.to_html("{{ url_pattern }}",
            { "experiment_id": experimentId });
        var datasetTiles = new MyTardis.DatasetTiles({
            "id": "other-experiment-datasets",
            "collection": datasets,
            "el": $("#other-experiment-datasets").get(0)
        });
        datasets.fetch({});
        return datasetTiles;
    }
}());
