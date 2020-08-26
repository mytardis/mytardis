/*
/!* eslint no-underscore-dangle: 0 *!/
/!* global _, Backbone, Mustache *!/
Backbone.$ = window.$;
require("mustache");

var ToggleButtonEditor = Backbone.Form.editors.Base.extend({

    tagName: "div",

    initialize: function(options) {
        var input = $("<input />")
            .attr("type", "hidden")
            .css("display", "none");
        this.$el.append(input);
        // Reassign $el briefly so we initialize the input field
        var tempEl = this.$el;
        this.$el = this._getInputField();
        // Call parent constructor
        Backbone.Form.editors.Base.prototype.initialize.call(this, options);
        // Restore $el
        this.$el = tempEl;
        // Initialize button group
        this._initButtons(options.schema.options);
    },

    _initButtons: function(optionList) {
        var buttonGroup = $("<span/>").addClass("btn-group");
        buttonGroup.append(_.map(optionList, function(option) {
            var button = $("<button/>").addClass("btn btn-default");
            button.prop("value", option.val);
            button.html(option.label);
            return button.get(0);
        }));
        // Change the input field on button click
        buttonGroup.find("button").click(_.bind(function(evt) {
            evt.preventDefault();
            var value = $(evt.currentTarget).prop("value");
            // Set the form type
            this.setValue(value);
        }, this));
        // Change the active button based on the input field
        this._getInputField().change(_.bind(function(evt) {
            // Set the correct button as active
            _.each(buttonGroup.find("button"), _.bind(function(button) {
                $(button).toggleClass("active", $(button).val() === this.getValue());
            }, this));
        }, this));
        this.$el.append(buttonGroup);
    },

    _getInputField: function() {
        return this.$el.find("input");
    },

    render: function() {
        this.setValue(this.value);
        return this;
    },

    getValue: function() {
        return this._getInputField().val();
    },

    setValue: function(value) {
        this._getInputField().val(value).change();
    }
});

var RelatedInfoModel = Backbone.Model.extend({
    defaults: {
        "type": "publication"
    },
    schema: {
        type: {
            title: "&nbsp;",
            type: ToggleButtonEditor,
            editorClass: "col-md-12",
            options: [
                {val: "publication", label: `<i class="icon-file"></i> Publication`},
                {val: "website", label: `<i class="icon-pushpin"></i> Website`}
            ]
        },
        identifier: {
            title: "URL",
            editorClass: "col-md-12",
            validators: ["required", "url"]
        },
        title: {type: "Text", editorClass: "col-md-12"},
        notes: {type: "TextArea", editorClass: "col-md-12", editorAttrs: {"rows": 8}}
    }
});

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

var dialog = $("#modal-add-related-info");
dialog.modal({"show": false});

// Configure placeholders
var formPlaceholders = {
    "publication": {
        "identifier": "http://journal.com/the-publication",
        "title": "Publication title",
        "notes": "Provide citation information for the publication..."
    },
    "website": {
        "identifier": "http://my.website.url/the-specific-doc",
        "title": "Website document title",
        "notes": "Describe how this website is related..."
    }
};

var showModelForm = function(model) {
    var form = (new Backbone.Form({
        "model": model
    })).render();
    dialog.find(".modal-body").html(form.el);
    // Set conditional placeholder text
    var typeEditor = form.fields.type.editor.$el;
    typeEditor.change(function() {
        _.each(formPlaceholders[form.fields.type.getValue()], function(v, k) {
            form.fields[k].editor.$el.prop("placeholder", v);
        });
    });
    typeEditor.change();
    //typeEditor.after($("#type-toggle").html());
    // Show form
    dialog.prop("form", form);
    dialog.modal("show");
};

// Add button
$("button.add-related-info").click(function() {
    showModelForm(new RelatedInfoModel());
});

// Edit buttons
$("#related-info-items").on("click", ".edit-related-info", function(evt) {
    evt.preventDefault();
    showModelForm($(this).parents(".related-info-item").prop("model"));
});

// Delete buttons
$("#related-info-items").on("click", ".delete-related-info", function(evt) {
    evt.preventDefault();
    var model = $(this).parents(".related-info-item").prop("model");
    model.destroy();
});

// Save button
$("button.save-related-info").click(function() {
    var form = dialog.prop("form");
    var commitResult = form.commit();
    if (_.isUndefined(commitResult)) {
        if (form.model.isNew()) {
            relatedInfo.create(form.model);
        } else {
            form.model.save();
        }
        dialog.modal("hide");
    }
});
*/
