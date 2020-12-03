/**
 * Publication Actions controller
 *
 * Provides methods to perform actions on a single publication record
 * (create, resume, share, delete etc.)
 *
 * @param {!ngDialog} ngDialog The ngDialog module
 * @param {!angular.$http} $http The Angular http service.
 * @param {!angular.$log} $log The Angular log service.
 * @param {!angular.$window} $window The Angular window service.
 * @constructor
 */
/* eslint no-unused-vars: ["error", { "argsIgnorePattern": "^_" }] */
angular
  .module('publicationWorkflow')
  .controller('PublicationActionsController', function ($resource, $log, ngDialog, $http, $window, $mdDialog) {
    const vm = this; // view model

    vm.isPublicationResource = $resource(
      '/apps/publication-workflow/experiment/:experiment_id/is_publication/',
      {}, { get: { method: 'GET' } },
    );
    vm.isPublicationDraftResource = $resource(
      '/apps/publication-workflow/experiment/:experiment_id/is_publication_draft/',
      {}, { get: { method: 'GET' } },
    );

    /*
     * Initialize vm.isPublication
     */
    vm.setIsPublication = function (experimentId) {
      vm.isPublication = null;
      if (experimentId) {
        vm.isPublicationResource
          .get({ experiment_id: experimentId })
          .$promise.then(
            (data) => {
              vm.isPublication = angular.fromJson(data).is_publication;
            },
            (error) => {
              $log.error(error);
            },
          );
      }
    };

    /*
     * Initialize vm.isPublicationDraft
     */
    vm.setIsPublicationDraft = function (experimentId) {
      vm.isPublicationDraft = null;
      if (experimentId) {
        vm.isPublicationDraftResource
          .get({ experiment_id: experimentId })
          .$promise.then(
            (data) => {
              vm.isPublicationDraft = angular.fromJson(data).is_publication_draft;
            },
            (error) => {
              $log.error(error);
            },
          );
      }
    };

    /**
     * Used with ng-init:
     */
    vm.init = function (myPubsCtrl, experimentId) {
      vm.myPubsCtrl = myPubsCtrl;
      if (experimentId) {
        vm.experimentId = experimentId;
        vm.setIsPublication(vm.experimentId);
        vm.setIsPublicationDraft(vm.experimentId);
      }
    };

    /**
     * Opens the publication form modal dialog
     */
    vm.openPublicationForm = function () {
      $log.debug(`PublicationActionsController.openPublicationForm: vm.formData.publicationId: ${vm.formData.publicationId}`);
      $log.debug(`PublicationActionsController.openPublicationForm: vm.formData.publicationTitle: ${vm.formData.publicationTitle}`);
      if (angular.isDefined(vm.formData.publicationId)) {
        vm.currentPageIdx = 1;
      }
      ngDialog.open({
        template: '/apps/publication-workflow/form/',
        data: {
          experimentId: parseInt(vm.experimentId),
          isPublication: vm.isPublication,
          isPublicationDraft: vm.isPublicationDraft,
          // 'formData': JSON.parse(JSON.stringify(formData)), // deep clone
          formData: vm.formData,
          currentPageIdx: vm.currentPageIdx,
        },
        closeByDocument: false,
        preCloseCallback() {
          if (angular.isDefined(vm.myPubsCtrl) && vm.myPubsCtrl !== null) {
            vm.myPubsCtrl.loadDraftPubsData();
            vm.myPubsCtrl.loadScheduledPubsData();
            vm.myPubsCtrl.loadReleasedPubsData();
            vm.myPubsCtrl.loadRetractedPubsData();
          } else {
            $window.location.reload();
          }
        },
      });
    };

    /**
     * Initialize default data for the publication form
     *
     */
    vm.emptyFormData = function () {
      const formData = {};
      formData.addedDatasets = []; // List of selected datasets
      formData.publicationTitle = ''; // Initialise publication title
      formData.publicationDescription = ''; // Initialise publication description
      formData.extraInfo = {}; // Stores discipline specific metadata
      formData.authors = [
        {
          name: '',
          institution: '',
          email: '',
        },
      ];
      formData.acknowledgements = ''; // Acknowledgements stored here
      formData.action = ''; // specifies what action is required on form update
      // if (useFigshare) {
      // vm.formData.selectedFigshareCategories = [];
      // vm.formData.selectedFigshareKeywords = [];
      // }
      return formData;
    };
    vm.formData = vm.emptyFormData();
    vm.currentPageIdx = 0;


    /**
     * Opens the publication form modal dialog to create a new publication
     *
     */
    vm.createPublication = function () {
      vm.openPublicationForm();
    };

    /**
     * Opens the publication form modal dialog to resume editing a publication
     *
     */
    vm.resumePublication = function () {
      $log.debug(`resumePublication: experimentId: ${vm.experimentId}`);
      const formData = vm.emptyFormData();
      formData.publicationId = vm.experimentId;
      $log.debug(`resumePublication: formData.publicationId: ${formData.publicationId}`);
      formData.action = 'resume';
      $http.post('/apps/publication-workflow/form/', formData).then((response) => {
        $log.debug(`resumePublication.http.post.success: response.data.publicationId: ${response.data.publicationId}`);
        $log.debug(`resumePublication.http.post.success: response.data.publicationTitle: ${response.data.publicationTitle}`);
        vm.formData = response.data;
        if (angular.isString(vm.formData.embargo)) {
          vm.formData.embargo = new Date(vm.formData.embargo);
        }
        vm.openPublicationForm();
      },
      () => {
        vm.errorMessages = ['Could not load publication draft!'];
      });
    };

    /**
     * Open tokens dialog, allowing creation of temporary links for sharing.
     *
     * The publicationId (a.k.a. experimentId) is passed to the view URL
     * so the view method can set is_owner in the context passed to the
     * tokens.html Django template.  The publicationId is also passed via the
     * ngDialog's data to the PublicationTokensController instance.
     */
    vm.sharePublication = function () {
      ngDialog.open({
        template: `/apps/publication-workflow/tokens/${vm.experimentId}/`,
        data: {
          publicationId: parseInt(vm.experimentId),
        },
        closeByDocument: false,
      });
    };

    /*
     * Delete publication draft
     */
    vm.deletePublicationDraft = function () {
      const confirmation = $mdDialog.confirm()
        .title(`Are you sure you want to delete Publication ID ${vm.experimentId}?`)
        .textContent('You cannot undo this action!')
        .ok('Yes, delete it!')
        .cancel('No, keep it.');

      $mdDialog.show(confirmation).then(() => {
        $log.info('OK, deleting publication...');
        $http.post(`/apps/publication-workflow/publication/delete/${vm.experimentId}/`, {})
          .then((_response) => {
            $log.debug('Publication deleted successfully.');
            $window.location.reload();
          },
          (_response) => {
            $log.debug('Failed to delete publication.');
          });
      }, () => {
        $log.info('OK, keeping publication');
      });
    };
    /*
     * Mint DOI
     */
    vm.mintDOI = function () {
      const confirmation = $mdDialog.confirm()
        .title(`Are you sure you want to mint a DOI for Publication ID ${vm.experimentId}?`)
        .textContent('You cannot undo this action!')
        .ok('Yes, mint a DOI!')
        .cancel('No, don\'t mint a DOI.');

      $mdDialog.show(confirmation).then(() => {
        $log.info('OK, minting a DOI...');
        vm.updating = true;
        $http.post(`/apps/publication-workflow/publication/mint_doi/${vm.experimentId}/`, {})
          .then((_response) => {
            vm.updating = false;
            $log.debug('DOI minted successfully.');
            $window.location.reload();
          },
          (_response) => {
            vm.updating = false;
            $log.debug('Failed to mint DOI.');
          });
      }, () => {
        vm.updating = false;
        $log.info('OK, not minting a DOI');
      });
    };

    /*
     * Retract publication
     */
    vm.retractPublication = function () {
      const confirmation = $mdDialog.confirm()
        .title(`Are you sure you want to retract Publication ID ${vm.experimentId}?`)
        .textContent('You cannot undo this action!')
        .ok('Yes, retract it!')
        .cancel('No, keep it.');

      $mdDialog.show(confirmation).then(() => {
        $log.info('OK, retracting publication...');
        $http.post(`/apps/publication-workflow/publication/retract/${vm.experimentId}/`, {})
          .then((_response) => {
            $log.debug('Publication retracted successfully.');
            $window.location.reload();
          },
          (_response) => {
            $log.debug('Failed to retract publication.');
          });
      }, () => {
        $log.info('OK, keeping publication');
      });
    };

    vm.updating = false;
  });
