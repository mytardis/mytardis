var AnzsrcCodes = (function() {
  var module = {};

  module.FieldOfResearch = Backbone.Model.extend({
    'label': function() {
      return this.get('code') + " - " + this.get('name');
    }
  });

  module.FieldsOfResearch = Backbone.Collection.extend({
    'model': module.FieldOfResearch,
    'comparator': function(fieldOfResearch) {
      return fieldOfResearch.get("code");
    }
  });

  module.FieldOfResearchView = Backbone.View.extend({
    'events': {
      'click a.close': 'remove'
    },
    'initialize': function() {
      this.render = _.bind(this.render, this);
      this.collection.on('add', this.render);
      this.collection.on('remove', this.render);
      this.collection.on('reset', this.render);
      this.collection.on('sync', this.render);
    },
    'render': function() {
      $(this.el).empty();
      this.collection.each(_.bind(function(model) {
        $(this.el).append($(Mustache.to_html(
            Mustache.TEMPLATES['anzsrc_codes/for_code'],
            model.attributes,
            Mustache.TEMPLATES
        )));
      }, this));
      if (_.isUndefined(isLoggedIn) || !isLoggedIn()) {
        $(this.el).find('.close').hide();
      }
      return this;
    },
    'remove': function(evt) {
      evt.preventDefault();
      var uri = $(evt.target).parents('*[content]').attr('content');
      _(this.collection.where({'uri': uri})).each(function(model) {
        model.destroy({ wait: true });
      });
    }
  });

  return module;
})();

