// TODO: remove hard coded URLs in case urls.py changes

// A filter used to remove items from the list of available datasets
// when added to the list of datasets to include in the publication
angular
.module('MyTardis')
.filter('removeMatchingDatasets', function () {
    return function (input, compareTo) {
        if (angular.isUndefined(input)) {
            return input;
        }
        var output = [];
        for (var i = 0; i < input.length; i++) {
            var add = true;
            for (var j = 0; j < compareTo.length; j++) {
                if (input[i].id === compareTo[j].dataset.id) {
                    add = false;
                }
            }
            if (add) {
                output.push(input[i]);
            }
        }
        return output;
    };
});

// The following two tardisForm directives attach appropriate ng-model
// attributes to form fields
// This code was adapted from http://stackoverflow.com/questions/21943242/child-input-directive-needs-to-compile-in-the-scope-of-its-parent-for-ng-model-t
angular
.module('MyTardis')
.directive('tardisForm', function () {
    return {
        replace: true,
        transclude: true,
        scope: {
            model: '=myModel',
            schema: '='
        },
        template: '<div ng-form novalidate><div ng-transclude></div></div>',
        controller: function ($scope, $element, $attrs) {
            if (angular.isUndefined($scope.model)) {
                $scope.model = {}
            }
            $scope.model.schema = $scope.schema;
            this.getModel = function () {
                return $attrs.myModel;
            };
        }
    };
});

angular
.module('MyTardis')
.directive('tardisFormField', function ($compile) {
    return {
        require: '^tardisForm',
        restrict: 'A',
        priority: 9999,
        terminal: true, //Pause Compilation to give us the opportunity to add our directives
        link: function postLink(scope, el, attr, parentCtrl) {
            // parentCtrl.getModel() returns the base model name in the parent
            var model = [parentCtrl.getModel(), "['" + attr.parameterName + "']"].join('');
            attr.$set('ngModel', model);
            // Resume the compilation phase after setting ngModel
            $compile(el, null /* transclude function */, 9999 /* maxPriority */)(scope);

        }
    };
});

// Publication form controller
angular
.module('MyTardis')
.controller('PublicationFormController', function ($scope, $log, $http, ngDialog, $window, $timeout) {

    // Opens the publication form modal dialogue
    $scope.openPublicationForm = function () {
        publication_id = null; // Ensure this is null when the form loads
        ngDialog.open({
                          template: '/apps/publication-forms/form/',
                          closeByDocument: false,
                          preCloseCallback: function () {
                              if (publication_id !== null &&
                                  publication_id !== experiment_id) {
                                  var redirectTo = '/experiment/view/' + publication_id + '/';
                                  $window.location = redirectTo;
                              } else if (angular.isDefined(publication_id)) {
                                  $window.location.reload();
                              }
                          }
                      });
    };

    $scope.errorMessages = []; // An array of strings to display to the user on error

    // these are defined earlier in the HTML
    $scope.isPublication = is_publication;
    $scope.isPublicationDraft = is_publication_draft;
    $scope.experiment = experiment_id;

    // Form state saved here. This will be overwritten if the publication form
    // is resumed.
    $scope.formData = {};
    $scope.formData.addedDatasets = []; // List of selected datasets
    $scope.formData.publicationTitle = ""; // Initialise publication title
    $scope.formData.publicationDescription = ""; // Initialise publication description
    $scope.formData.extraInfo = {}; // Stores discipline specific metadata
    $scope.formData.authors = [{'name':'',
                                'institution':'',
                                'email':''}]; // Stores the authors of the publication
    $scope.formData.acknowledgements = ""; // Acknowledgements stored here
    $scope.formData.action = ""; // specifies what action is required on form update

    $scope.exampleAcknowledgements = [{
        'agency': 'Australian Synchrotron facility',
        'text': 'This research was undertaken on the [insert beamline name] beamline at the Australian Synchrotron, Victoria, Australia.'
    },
        {
            'agency': 'Science and Industry Endowment Fund',
            'text': 'This work is supported by the Science and Industry Endowment Fund.'
        },
        {
            'agency': 'Multi-modal Australian ScienceS Imaging and Visualisation Environment',
            'text': 'This work was supported by the Multi-modal Australian ScienceS Imaging and Visualisation Environment (MASSIVE) (www.massive.org.au).'
        },
        {
            'agency': 'Australian National Beamline Facility',
            'text': 'This research was undertaken at the Australian National Beamline Facility at the Photon Factory in Japan, operated by the Australian Synchrotron.  We acknowledge the Australian Research Council for financial support and the High Energy Accelerator Research Organisation (KEK) in Tsukuba, Japan, for operations support.'
        },
        {
            'agency': 'International Synchrotron Access Program',
            'text': 'We acknowledge travel funding provided by the International Synchrotron Access Program (ISAP) managed by the Australian Synchrotron and funded by the Australian Government.'
        }];

    // Save the form state, creating a new publication if necessary
    // and call onComplete when saving is complete. The server should
    // return an experiment ID that represents the new/updated publication.
    // If this is the first time the publication has been saved, a new
    // publication will be created. Otherwise, the publication will be
    // updated.
    var saveFormState = function (onComplete, onFailure) {
        $scope.loadingData = true;
        $http.post('/apps/publication-forms/form/', $scope.formData).success(function (data) {
            if ('error' in data) { // This happens when the form fails to validate but no server error encountered
                $scope.errorMessages.push(data.error);
                onFailure();          // Since all validation also happens on the client, this should never happen.
                $scope.loadingData = false;
                return;
            }

            $scope.formData = data;

            // The global variable publication_id is used in the preCloseCallback
            // of the modal dialogue for redirection. If the publication draft has
            // been created, it redirects there on close.
            publication_id = $scope.formData.publication_id;

//          $scope.infoMessage = "Dataset selection saved!";
            onComplete();
            $scope.loadingData = false;
        }).error(function (data) {  // eslint-disable-line no-unused-vars
            $scope.errorMessages.push("the server could not process your request");
            onFailure();
            $scope.loadingData = false;
        });
    }

    // ***************
    // Form validators
    // ***************
    // A validator should take two functions as arguments:
    //   a function to be called when validation succeeds
    //   a function to be called when validation fails
    // Any error messages may be displayed in the $scope.errorMessages array
    // eslint-disable-next-line no-unused-vars
    var noValidation = function (onSuccess, onError) {
        onSuccess();
    }
    var datasetSelectionValidator = function (onSuccess, onError) {

        extraInfoHelpers = []; // This list of helper functions must be cleared in case the discipline specific form info changes

        $scope.formData.action = "update-dataset-selection";

        if ($scope.formData.publicationTitle.trim().length === 0) {
            $scope.errorMessages.push("A title must be given");
        }

        if ($scope.formData.publicationDescription.trim().length == 0) {
            $scope.errorMessages.push("Provide a description");
        }

        if ($scope.formData.addedDatasets.length === 0) {
            $scope.errorMessages.push("At least one dataset must be selected");
        }

        if ($scope.errorMessages.length > 0) { // call onError if the form didn't validate
            onError();
        } else {
            // If the form is okay, send to the server
            saveFormState(onSuccess, function () {
                // If an error occurred...
                onError();
            });
        }
    }


    var extraInfoHelpers = []; // array of functions that evaluate to true if there are no errors
                               // extraInfoHelpers are registered elsewhere
    var extraInformationValidator = function (onSuccess, onError) {

        errors = false;

        for (var i = 0; i < extraInfoHelpers.length; i++) {
            if (!extraInfoHelpers[i]()) {
                errors = true;
            }
        }

        if (errors) {
            onError();
        } else {
            $scope.formData.action = "update-extra-info";
            saveFormState(onSuccess, onError);
        }

    }

    var finalSubmissionValidator = function (onSuccess, onError) {

        $scope.formData.action = "submit";

        errors = false;
        if ($scope.formData.authors.length === 0) {
            $scope.errorMessages.push("You must add at least one author.");
            errors = true;
        }

        var tmpAuthors = [];
        for (var a in $scope.formData.authors) {
        if ($scope.formData.authors.hasOwnProperty(a)) {
            var author = $scope.formData.authors[a];
            var x = 0;
            if (angular.isUndefined(author.email) || author.email.trim().length === 0) {
                x++;
            }
            if (angular.isUndefined(author.name) || author.name.trim().length === 0) {
                x++;
            }
            if (angular.isUndefined(author.institution) || author.institution.trim().length === 0) {
                x++;
            }
            if (x === 0) {
                tmpAuthors.push(author);
            } else if (x < 3) {
                errors = true;
                $scope.errorMessages.push("Invalid author entries.");
                break;
            }
        }
        }
        if (!errors) {
            $scope.formData.authors = tmpAuthors;
        }

        if (angular.isUndefined($scope.formData.embargo) || $scope.formData.embargo == null) {
            $scope.errorMessages.push("Release date cannot be blank.");
            errors = true;
        }

        if (errors) {
            onError();
        } else {
            saveFormState(onSuccess, onError);
        }
    }

    // A list of available pages of the form, along with a function used to validate the form content
    $scope.form_pages = [{
        title: '',
        url: 'form_page1.html',
        validationFunction: noValidation
    },
        {
            title: 'Select datasets',
            url: 'form_page2.html',
            validationFunction: datasetSelectionValidator
        },
        {
            title: 'Extra information',
            url: 'form_page3.html',
            validationFunction: extraInformationValidator
        },
        {
            title: 'Attribution and licensing',
            url: 'form_page4.html',
            validationFunction: finalSubmissionValidator
        },
        {
            title: 'Submission complete',
            url: 'form_page5.html',
            validationFunction: noValidation
        }];

    // Keep track of the current page
    $scope.currentPageIdx = 0;
    $scope.totalPages = $scope.form_pages.length;
    $scope.current_page = $scope.form_pages[$scope.currentPageIdx];

    // If isPublicationDraft is true, then
    // the form state should be loaded from the database.
    if ($scope.isPublicationDraft) {
        // Setting formData.action to "resume" causes the form data to be reloaded
        // rather than overwritten.
        $scope.formData.publication_id = experiment_id;
        $scope.formData.action = "resume";
        $http.post('/apps/publication-forms/form/', $scope.formData).success(function (data) {
            $scope.formData = data;
            $scope.currentPageIdx = 1; // Once form data is reloaded, advance to the second page
            $scope.current_page = $scope.form_pages[$scope.currentPageIdx];
        }).error(function (data) {  // eslint-disable-line no-unused-vars
            $scope.errorMessages = ['Could not load publication draft!'];
        });
    }

    // Load the available experiments and datasets
    $scope.loadingData = true; // Loading animation shown when this is true
    $http.get('/apps/publication-forms/data/fetch_experiments_and_datasets/').success(function (data) {
        $scope.experiments = data;

        // Set default experiment
        for (var i = 0; i < $scope.experiments.length; i++) {
            if ($scope.experiments[i].id === experiment_id) {
                $scope.selectedExperiment = $scope.experiments[i];
                break;
            }
        }

        $scope.loadingData = false;
    });


    // Add a dataset to the list of selected datasets
    $scope.addDatasets = function (experiment, datasets) {
        if (angular.isUndefined(datasets)) {
            return;
        }
        for (var i = 0; i < datasets.length; i++) {
            $scope.formData.addedDatasets.push({
                                                   "experiment": experiment.title,
                                                   "experiment_id": experiment.id,
                                                   "dataset": datasets[i]
                                               });
        }
    }
    // Remove a dataset from the list of selected datasets
    $scope.removeDataset = function (dataset) {
        var index = $scope.formData.addedDatasets.indexOf(dataset);
        if (index > -1) {
            $scope.formData.addedDatasets.splice(index, 1);
        }
    }

    // Advance to the next page of the form
    $scope.nextPage = function () {
        $('.ngdialog').scrollTop(0);
        if ($scope.currentPageIdx < $scope.form_pages.length - 1 && !$scope.loadingData) {
            $scope.errorMessages = [];
            $scope.infoMessage = "";
            $scope.current_page.validationFunction(function () { // On success...
                $scope.currentPageIdx++;
                $scope.current_page = $scope.form_pages[$scope.currentPageIdx];
            }, function () { // On error...
                // do nothing...
            });
        }
    }
    // Move back a page
    $scope.previousPage = function () {
        if ($scope.currentPageIdx - 1 >= 0 && !$scope.loadingData) {
            $scope.errorMessages = [];
            $scope.infoMessage = "";
            $scope.currentPageIdx--;
            $scope.current_page = $scope.form_pages[$scope.currentPageIdx];
        } else if ($scope.currentPageIdx === 0) {
            ngDialog.close();
        }
    }

    $scope.isComplete = function () {
        return $scope.currentPageIdx === ($scope.form_pages.length - 1);
    }

    $scope.isLastPage = function () { // Actually, second last page
        return $scope.currentPageIdx === ($scope.form_pages.length - 2);
    }

    // Set the publication title
    $scope.setTitle = function (title) {
        $scope.formData.publicationTitle = title;
    }

    $scope.setDescription = function (description) {
        $scope.formData.publicationDescription = description;
    }

    // Scroll the dataset list to top
    $scope.scrollDsSelectorToTop = function() {
        $('#datasetList').scrollTop(0);
    };

    // Add author to publication
    $scope.addAuthorEntry = function () {
        $log.info($scope.formData)
        $scope.formData.authors.push({'name':'',
                                      'institution':'',
                                      'email':''})
    }

    // Remove author from publication
    $scope.removeAuthorEntry = function (idx) {
        $scope.formData.authors.splice(idx, 1);
    }

    // Copy acknowledgement text to acknowledgement field
    $scope.copyAcknowledgement = function (text) {
        if ($scope.formData.acknowledgements.indexOf(text) === -1) {
            if ($scope.formData.acknowledgements.length > 0) {
                $scope.formData.acknowledgements += " ";
            }
            $scope.formData.acknowledgements += text;
        }
    }

    // eslint-disable-next-line no-unused-vars
    $scope.$watch('formData.selectedLicenseId', function (newVal, oldVal) {
        if (angular.isDefined($scope.formData.licenses)) {
            for (var i in $scope.formData.licenses) {
                if ($scope.formData.licenses.hasOwnProperty(i)) {
                    var license = $scope.formData.licenses[i];
                    if (license['id'] === newVal) {
                        $scope.formData.selectedLicense = license;
                        break;
                    }
                }
            }
        }
    });

    $scope.saveAndClose = function () {
        $('.ngdialog').scrollTop(0);
        saveFormState(function () { // On success
                          $scope.closeThisDialog();
                      }
            , function () {
            } // On error
        );
    }


    $scope.setEmbargoToToday = function () {
        $scope.formData.embargo = new Date();
    }
    // Ensures that the embargo date is a Date object
    // eslint-disable-next-line no-unused-vars
    $scope.$watch('formData.embargo', function (newVal, oldVal) {
        if (angular.isString(newVal)) {
            $scope.formData.embargo = new Date(newVal);
        }
    });

    // #### PDB HELPER ####
    $scope.requirePDBHelper = function () {
        extraInfoHelpers.push(function () {
            if (angular.isUndefined($scope.pdbOK) || $scope.pdbOK === false) {
                $scope.errorMessages.push("PDB ID invalid or not given");
                return false;
            } else {
                return true;
            }
        });
    }
    $scope.pdbSearching = false;
    $scope.pdbSearchComplete = false;
    // eslint-disable-next-line no-unused-vars
    $scope.$watch('formData.pdbInfo', function (newVal, oldVal) {
        if (angular.isDefined(newVal)) {
            $scope.pdbSearchComplete = Object.keys(newVal).length;
            $scope.pdbOK = (newVal.status !== 'UNKNOWN')
        } else if (angular.isDefined($scope.pdbOK) || $scope.hasPDB) {
            delete $scope.pdbOK // unset the variable so the form validator can continue
        }
    });


    var pdbSearchTimeout;
    $scope.performPDBSearch = function (pdbId) {
        $scope.pdbSearching = true;
        $scope.pdbSearchComplete = false;
        $scope.pdbOK = false;
        if (pdbSearchTimeout) {
            $timeout.cancel(pdbSearchTimeout);
        }

        pdbSearchTimeout = $timeout(function () {
            $http.get('/apps/publication-forms/helper/pdb/' + pdbId + '/').success(
                function (data) {
                    $scope.pdbSearching = false;
                    $scope.pdbSearchComplete = true;
                    $scope.formData.pdbInfo = data;
                }
            )
        }, 1000);
    }
});
