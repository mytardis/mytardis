var MyTardis = (function(){
  var module = {};

  module.Dataset = Backbone.Model.extend({});

  module.Datasets = Backbone.Collection.extend({
    model: module.Dataset
  });

  module.DatasetTiles = Backbone.View.extend({
    tagName: "div",
    id: "datasets",
    _lastFilterFunc: function() { return true; },
    initialize : function(options) {
      // Allow the functions to be used by themselves
      this.filter = _.bind(this.filter, this);
      this.render = _.bind(this.render, this);
      // Build initial tiles
      this.buildTiles();
      this.visibleTiles = _.keys(this.tiles);
      // Bind collection events to view
      var refresh = _.bind(function() {
        this.buildTiles();
        this.filter(this._lastFilterFunc);
      }, this);
      this.collection.bind('add', refresh);
      this.collection.bind('change', refresh);
      this.collection.bind('delete', refresh);
      this.collection.bind('reset', refresh);
    },

    buildTiles: function() {
      this.tiles = this.collection.reduce(function(memo, v, k) {
        view = new MyTardis.DatasetTile({ 'model': v });
        view.render();
        memo[view.model.id] = view;
        return memo;
      }, {});
    },

    filter: function(filterFunc) {
      if (_.isUndefined(filterFunc)) {
        filterFunc = this._lastFilterFunc;
      } else {
        this._lastFilterFunc = filterFunc;
      }
      this.visibleTiles = _.chain(this.collection.filter(filterFunc))
                           .pluck('id')         // Get IDs
                           .sortBy(_.identity)  // Sort by ID (chronological)
                           .reverse().value();  // Get reversed order
      this.render();
      return this;
    },

    render: function() {
      var newContents = $(Mustache.to_html(
        Mustache.TEMPLATES['tardis_portal/dataset_tiles'],
        {
          datasets: _(this.visibleTiles).map(function(v) {
            return '<i class="dataset-tile-placeholder" data-dsid="'+v+'"/>';
          })
        },
        Mustache.TEMPLATES
      ));
      _.each(newContents.find('.dataset-tile-placeholder'), function(v) {
        var view = this.tiles[parseInt($(v).attr('data-dsid'))];
        $(v).parent().replaceWith(view.el);
      }, this);
      $(this.el).html(newContents);
      return this;
    }
  });

  module.DatasetTile = Backbone.View.extend({
    tagName: "div",
    className: "dataset-tile thumbnail",
    initialize : function(options) {
      this.render = _.bind(this.render, this);
      this.model.bind('change', this.render);
    },
    render: function() {
      $(this.el).html(Mustache.to_html(
          Mustache.TEMPLATES['tardis_portal/dataset_tile'],
          this.model.attributes,
          Mustache.TEMPLATES
      ));
      return this;
    }
  });

  return module;
})();