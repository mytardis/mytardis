var MyTardis = (function(){
  var module = {};

  module.Dataset = Backbone.Model.extend({});

  module.Datasets = Backbone.Collection.extend({
    model: module.Dataset
  });

  return module;
})();