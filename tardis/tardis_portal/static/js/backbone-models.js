var MyTardis = (function(){
    var module = {};

    module.DatasetSyncManager = _.extend({
	'_collectionSet': [],
	'register': function(collection) {
            // Add collection to those to be notified
            this._collectionSet = _(this._collectionSet).union([collection]);
            // Notify others collections on sync
            collection.on('sync', _.bind(this._syncHandler, this));
            // Handle destoyed models being removed from the collection before sync
            collection.on('destroy', _.bind(function(model) {
		// Handler is slightly different, because model isn't updated
		model.on('sync', _.bind(this._destroyHandler, this));
            }, this));
	},
	'deregister': function(collection) {
            this._collectionSet = _(this._collectionSet).without(collection);
	},
	'_syncHandler': function(model, collection) {
            _.chain(this._collectionSet).without(model.collection)
		.each(function(otherCollection) {
		    // Get model in other collection
		    var otherModel = otherCollection.get(model.id);
		    // If there isn't one, that's fine
		    if (!otherModel) return;
		    // If there is, update common attributes
		    otherModel.set({'experiments': model.get('experiments')});
		});
	},
	'_destroyHandler': function(model, resp) {
            _.chain(this._collectionSet).without(model.collection)
		.each(function(collection) {
		    // Get model in other collection
		    var otherModel = collection.get(model.id);
		    // If there isn't one, that's fine
		    if (!otherModel) return;
		    // If there is, update common attributes
		    otherModel.set({'experiments': resp.experiments});
		});
	},
    }, Backbone.Events);

    module.Dataset = Backbone.Model.extend({});

    module.Datasets = Backbone.Collection.extend({
	experimentId: null,
	model: module.Dataset,
	initialize : function(options) {
            // Sync some data between dataset collections
            module.DatasetSyncManager.register(this);
	}
    });

    // Internal subview
    var DatasetFilter = Backbone.View.extend({
	tagName: "p",
	events:  {
            "keyup input": "doFilter",
            "keypress input[type=text]": "filterOnEnter"
	},
	initialize: function(options) {
            this._datasetTiles = options['datasetTiles'];
	},
	_filterDescription: function(str) {
            lStr = str.toLowerCase();
            return function(model) {
		directory = model.get('directory');
		searchString = model.get('description').toLowerCase();
		if (directory !== null) {
		    searchString = directory.toLowerCase() + searchString;
		}
		return _.string.include(searchString , lStr);
            };
	},
	render: function() {
            $(this.el).html(Mustache.to_html(
		Mustache.TEMPLATES['tardis_portal/dataset_filter'],
		this._datasetTiles,
		Mustache.TEMPLATES
            ));
            return this;
	},
	doFilter: function() {
            var searchTerm = $(this.el).find('input').val();
            this._datasetTiles.filter(this._filterDescription(searchTerm));
	},
	filterOnEnter: function(e) {
            if (e.keyCode == 13)
            {
		e.preventDefault();
		return false;
            }
	}
    });

    module.DatasetTiles = Backbone.View.extend({
	tagName: "div",
	_lastFilterFunc: function() { return true; },
	initialize : function(options) {
            // Allow the functions to be used by themselves
            this.filter = _.bind(this.filter, this);
            this.render = _.bind(this.render, this);
            // Create filter control
            this._datasetFilter = new DatasetFilter({
		'datasetTiles': this
            }).render();
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
            this.collection.bind('remove', refresh);
            this.collection.bind('reset', refresh);
            // Enable drag-and-drop
            this.on('tiles:rendered', _.bind(this._enableDragDrop, this));
	},

	addTile: function(tile) {
            var newModel = tile.model.clone();
            this.collection.add(newModel);
            newModel.save().done(function() {
		tile.trigger('tile:copy', tile, this);
            });
	},

	_enableDragDrop: function() {
            // Context should be a MyTardis.DatasetTiles instance
            $(this.el).find('.datasets').sortable({
		'connectWith': '.datasets',
		'dropOnEmpty': true,
		'helper': 'clone',
		'placeholder': 'thumbnail span6',
		'receive': _.bind(function(event, ui) {
		    var datasetTile = ui.item.find('.dataset-tile').prop('view');
		    this.addTile(datasetTile);
		    ui.item.detach();
		}, this)
            }).disableSelection();
            // We need the dataset columns to be roughly the same height, or else
            // there's no way to drag datasets across
            var ensureSimilarHeight = function() {
		// Remove min-height to get real height
		$('.datasets').css('min-height', '');
		// Select the maximum height
		var height = _.max(_.map($('.datasets'), function(v) {
		    return $(v).height();
		}));
		// Set min-height to ensure that all columns are that high (min 100px)
		$('.datasets').css('min-height', Math.max(height, 100)+"px");
            };
            this.on('tiles:rendered', ensureSimilarHeight);
            $(window).on('resize', ensureSimilarHeight);
            ensureSimilarHeight();
	},

	_buildTile: function(tiles, model) {
            view = new MyTardis.DatasetTile({ 'model': model });
            view.render();
            tiles[view.model.id] = view;
            view.on('tile:copy', _.bind(function(tile, destTiles) {
		$(tile.el).detach();
		this.render();
            }, this));
            return tiles;
	},

	buildTiles: function() {
            this.tiles = this.collection.reduce(_.bind(this._buildTile, this), {});
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
            // Detach existing tiles
            _(this.tiles).each(function(tile) { $(tile.el).detach(); });
            // Render container with placeholders
            var newContents = $(Mustache.to_html(
		Mustache.TEMPLATES['tardis_portal/dataset_tiles'],
		{
		    datasets: _(this.visibleTiles).map(function(v) {
			return '<i class="dataset-tile-placeholder" data-dsid="'+v+'"/>';
		    })
		},
		Mustache.TEMPLATES
            ));
            // Fill in the placeholders (because Mustache can't inject DOM)
            _.each(newContents.find('.dataset-tile-placeholder'), function(v) {

		var view = this.tiles[parseInt($(v).attr('data-dsid'))];

		$(v).parent().replaceWith(view.el);
            }, this);
            // Add filter control if necessary
            if ($(this._datasetFilter.el).parent().size() == 0)
		$(this.el).prepend(this._datasetFilter.el);
            // Remove all contents except the filter and add new contents
            $(this.el).children().not(this._datasetFilter.el).remove();
            $(this.el).append(newContents);
            // Give a path back to the view from the DOM
            $(this.el).prop('view', this);
            // Trigger an event we can tie other functionality to
            this.trigger('tiles:rendered');
            return this;
	}
    });

    var dfcount = 0;
    var dssize = "0";
    module.DatasetTile = Backbone.View.extend({
	tagName: "div",
	className: "dataset-tile thumbnail",
	events:  {
            "click a.close": "remove",
	},
	initialize: function(options) {
            // Render on change
            this.render = _.bind(this.render, this);
            this.model.bind('sync', this.render);
            //this.model.bind('change', this.render);

	},
	templateWrapper: {
            'dataset_datafiles_badge': function() {
		return Mustache.to_html(
		    Mustache.TEMPLATES['tardis_portal/badges/datafile_count'],
		    {
			'title': _.sprintf(
			    "Contains %s file%s",
			    this.file_count,
			    this.file_count == 1 ? '' : 's'),
			'count': this.file_count
		    },
		    Mustache.TEMPLATES
		);
            },
            'dataset_size_badge': function() {

		return Mustache.to_html(
		    Mustache.TEMPLATES['tardis_portal/badges/size'],
		    {
			'title': _.sprintf("Dataset size is ",
					   this.size_human_readable),
			'label': this.size_human_readable
		    },
		    Mustache.TEMPLATES
		);
            }
	},
	render: function() {
            // This makes the rendering of badge data asynchronous
            // A temporary fix to be changed when bootstrap.js is removed entirely..
            var el = $(this.el);
	    var data = _.defaults(_.clone(this.templateWrapper),
				  this.model.attributes);
	    // Render
	    el.html(Mustache.to_html(
		Mustache.TEMPLATES['tardis_portal/dataset_tile'],
		data,
		Mustache.TEMPLATES
	    ));
            // Hide "remove" button if think removing will be rejected
            if (!this.canRemove()) {
		// Keep the height, hide the button
		$(this.el).find('a.close')
		    .css('opacity', 0)
		    .mouseover(function(evt) { // If somehow we do mouseover, replace
			$(evt.delegateTarget).replaceWith(
			    $('<div><div/>').height($(evt.delegateTarget).outerHeight()));
		    });
            }
            // Give a path back to the view from the DOM
            $(this.el).prop('view', this);
            return this;
	},
	canRemove: function() {
            if (_.isUndefined(isLoggedIn) || !isLoggedIn())
		return false;
            return this.model.attributes.experiments.length > 1
	},
	remove: function() {
            // Request the model be removed
            // Note: The server may decline to do so.
            this.model.destroy({ wait: true });
            this.trigger('tile:remove', this);
	}
    });

    return module;
})();
