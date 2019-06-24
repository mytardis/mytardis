/* tardis/tardis_portal/static/js/jquery/tardis_portal/view_experiment/dataset_tiles.js */
  
/* global Backbone, MyTardis */

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
