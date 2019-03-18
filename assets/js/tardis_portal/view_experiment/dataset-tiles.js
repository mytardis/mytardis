/* tardis/tardis_portal/static/js/jquery/tardis_portal/view_experiment/dataset_tiles.js */

/* eslint global-strict: 0, strict: 0 */
/* global Backbone, backbonemodels */

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
        var datasets = new MyTardis.Datasets();
        datasets.experimentId = parseInt(experimentId),
            // Substitute experiment ID to get collection
            datasets.url = Mustache.to_html("{{ url_pattern }}",
                { 'experiment_id': experimentId });
        var datasetTiles = new MyTardis.DatasetTiles({
            'id': "other-experiment-datasets",
            'collection': datasets,
            'el': $('#other-experiment-datasets').get(0)
        });
        datasets.fetch({});
        return datasetTiles;
    }
    $('form#other-experiment-selection').submit(function(evt) {
        evt.preventDefault();
        var experimentId = $(this).find('[name="experiment_id"]').val();
        otherDatasetTiles = getDatasetsForExperiment(experimentId);
    });
    $('form#other-experiment-selection select').change(function(evt) {
        $(this).parents('form').submit();
    });
    // Load initial data
    $('form#other-experiment-selection').submit();
})();
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
